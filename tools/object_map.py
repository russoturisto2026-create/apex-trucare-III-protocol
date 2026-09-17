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

import fields as F

def known_for(cls, obj):
    """Разобранные поля объекта — из реестра tools/fields.py: (offset, size, подпись, кодирование, статус)."""
    if cls == 0xA1:  # кадры от помпы класса A1 — из списка ANSWERS
        for a in getattr(F, 'ANSWERS', []):
            if a['code'] == obj:
                return [(0, 2, a['purpose'], a['payload'], a['status'])]
        return []
    if cls != 0xA3:
        return []
    out = []
    for fd in F.FIELDS:
        st = fd['st']
        if st['obj'] != obj:
            continue
        if fd.get('enc'):
            enc = fd['enc']
        elif fd['kind'] in ('enum', 'bool'):
            enc = ', '.join(f'{v}={l}' for v, l in sorted(fd['values'].items()))
        elif fd['kind'] == 'num':
            k, unit = fd['scale']
            enc = (f'× {k:g} {unit}'.replace('.', ',') if k not in (1, None) else f'число, {unit}').strip()
        else:
            enc = 'YY MM DD HH MM SS'
        out.append((st['off'], st['size'], fd['name'], enc, fd['status']))
    return out

KNOWN = {(0xA3, o): known_for(0xA3, o) for o in (0x00, 0x0C)}

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
