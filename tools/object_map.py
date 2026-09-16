#!/usr/bin/env python3
"""Промежуточная карта разбора объекта ответа помпы: пословная (u16LE) таблица data-payload с
отметкой «константа/переменная» в окне исследования и текущей расшифровкой. Показывает степень
разбора объекта. Идентичности в ответах нет; чувствительных данных объекты статуса не содержат.

Использование: object_map.py <btsnoop.log> <класс hex> <код hex> [HHMM-начало-окна] [idx-записи hex]
Пример: object_map.py bt.log a3 00 1634
"""
import sys, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hci_frames as H

# Реестр уже разобранных/кандидатных полей: (класс,код) -> (offset, size, подпись, кодир./значение, статус)
KNOWN = {
 (0xA3,0x00): [
    (1,1,"вид сигнала тревоги","0=Звуковой, 1=Вибрация, 2=Звуковой и вибрация","🟢"),
    (2,1,"скорость болюса","0=Нормальная, 1=Низкая","🟢"),
    (3,1,"яркость экрана","индекс меню: 0=10%, 1=30%, 2=50%, 3=60%, 4=80%, 5=100%","🟢"),
    (4,1,"флаги настроек болюса","битовое поле: 0x02=расширенный болюс, 0x04=напоминание о ГК","🟢"),
    (5,1,"блокировка клавиатуры — вкл","0=выкл, 1=вкл","🟢"),
    (6,1,"автовыключение помпы — вкл","0=выкл, 1=вкл","🟢"),
    (7,1,"время автовыключения помпы","часы (1/3/5/7)","🟢"),
    (8,1,"«инсулин заканчивается» — порог","единицы (10/11/13)","🟢"),
    (9,1,"«инсулин заканчивается» — время","получасы (4=02:00 … 24=12:00; 11=5:30, 13=6:30)","🟢"),
    (13,1,"лимит дневной дозы — вкл","0=выкл, 1=вкл","🟢"),
    (16,2,"счётчик поданного инсулина","шаг 0,025 Ед","🟡"),
    (14,2,"автовыключение экрана","×0,1 с (150=15,0 с)","🟢"),
    (20,2,"лимит дневной дозы","единицы (100/150/200/250)","🟢"),
    (28,2,"предустановка болюса, слот 1 (Завтрак A)","0,025 Ед","🟢"),
    (30,2,"предустановка болюса, слот 2 (Завтрак B)","0,025 Ед","🟢"),
    (32,2,"предустановка болюса, слот 3 (Обед A)","0,025 Ед","🟢"),
    (24,2,"максимальный базал","0,025 Ед → 320=8,0; 308=7,7","🟢"),
    (26,2,"максимальный болюс","0,025 Ед → 480=12,0; 492=12,3","🟢"),
    (44,6,"метка времени","YY MM DD HH MM SS (байт=значение)","🟢"),
    (50,1,"язык помпы","0=Русский, 1=English","🟢"),
    (52,4,"остаток резервуара","0,001 Ед","🟢"),
    (76,2,"текущая базальная скорость","шаг 0,025 Ед/ч → 20=0,5","🟡"),
 ],
 (0xA3,0x0C): [
    (2,1,"длительность сигнала тревоги","0=Длинный, 1=Нормальный, 2=Короткий","🟢"),
    (3,1,"напряжение батареи","0,01 В → 136=1,36 В","🟢"),
    (4,1,"звуковой режим","0=выкл, 1=вкл","🟢"),
    (5,1,"шаг звукового режима","индекс: 0=0,1; 1=0,5; 3=5,0 Ед","🟢"),
 ],
}

def inwin(pl, hhmm):
    if hhmm is None or len(pl)<50: return True
    HH=int(hhmm[:2]); MM=int(hhmm[2:])
    return pl[47]>HH or (pl[47]==HH and pl[48]>=MM)

def field_at(known, off):
    for o,sz,lbl,enc,st in known:
        if o<=off<o+sz: return (o,sz,lbl,enc,st)
    return None

def build(path, cls, obj, hhmm=None, idx=None):
    frames=H.frames(path)
    fs=[f for k,f in frames if k=='ANS' and len(f)>6 and f[3]==cls and f[4]==obj]
    idxs=sorted({f[5] for f in fs})
    if idx is not None: fs=[f for f in fs if f[5]==idx]
    pls=[f[6:-2] for f in fs]
    if hhmm: pls=[p for p in pls if inwin(p,hhmm)]
    if not pls: return None
    L=min(len(p) for p in pls)
    var={o for o in range(L) if len({p[o] for p in pls})>1}
    return dict(pls=pls, sample=pls[-1][:L], var=var, known=KNOWN.get((cls,obj),[]), L=L, idxs=idxs)

def md(cls, obj, b, note=""):
    sample,var,known,L=b["sample"],b["var"],b["known"],b["L"]
    kb=sum(sz for _,sz,_,_,_ in known)
    out=[]
    recs=f", записей(idx): {len(b['idxs'])}" if len(b['idxs'])>1 else ""
    out.append(f"### Объект {cls:02x}/{obj:02x} — payload {L} байт, разобрано {kb}/{L}{recs}{note}")
    out.append("| off | пример | C/V | поле | кодирование/значение | статус |")
    out.append("|---|---|---|---|---|---|")
    off=0
    while off+1 < L or (off < L and off+2<=L):
        if off+2>L: break
        f=field_at(known,off)
        if f:
            o,sz,lbl,enc,st=f; raw=sample[o:o+sz].hex()
            cv='V' if any((o+i) in var for i in range(sz)) else 'C'
            rng=f"{o}" if sz==1 else f"{o}..{o+sz-1}"
            out.append(f"| {rng} | `{raw}` | {cv} | {lbl} | {enc} | {st} |")
            off=o+sz
        elif off%2 or field_at(known,off+1):
            cv='V' if off in var else 'C'
            out.append(f"| {off} | `{sample[off:off+1].hex()}` | {cv} | — | u8={sample[off]} | 🔲 |")
            off+=1
        else:
            v=struct.unpack('<H',sample[off:off+2])[0]
            cv='V' if (off in var or (off+1) in var) else 'C'
            out.append(f"| {off}..{off+1} | `{sample[off:off+2].hex()}` | {cv} | — | u16LE={v} | 🔲 |")
            off+=2
    return "\n".join(out)

if __name__=='__main__':
    path=sys.argv[1]; cls=int(sys.argv[2],16); obj=int(sys.argv[3],16)
    hhmm=sys.argv[4] if len(sys.argv)>4 and sys.argv[4]!='-' else None
    idx=int(sys.argv[5],16) if len(sys.argv)>5 else None
    b=build(path,cls,obj,hhmm,idx)
    print("нет кадров в окне" if not b else md(cls,obj,b))
