#!/usr/bin/env python3
"""Генерация таблиц полей из реестра tools/fields.py.

Заменяет содержимое между маркерами `<!-- gen:ИМЯ -->` и `<!-- /gen:ИМЯ -->`:
  PROTOCOL.md: commands, a3_00, a3_00_unknown, a3_0c, a3_0c_unknown, a1_32, a1_34, a1_11, a1_02
  OBJECTS.md:  obj_a3_00, obj_a3_0c, obj_a3_31, obj_a3_0a, obj_a3_0b, obj_a3_08, obj_a3_07, obj_a3_21,
               obj_a3_26 (побайтовая карта по архивным захватам окна исследования)
  RESEARCH.md: research_objects, research_commands (сводка текущего состояния)

Использование: gen_tables.py [--check]   (--check — только сообщить, есть ли расхождения)
"""
import sys, os, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fields as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = '\r\n'


def steps_ref(steps):
    return ', '.join(f'{s:03d}' for s in steps)


def mats_ref(fd):
    ms = sorted(set(fd.get('materials', []) + [x[2] for x in fd.get('screens', [])]))
    return ', '.join(f'№{m}' for m in ms)


def fmt_scale(k):
    return ('%g' % k).replace('.', ',')


def encoding(fd):
    if fd.get('enc'):
        return fd['enc']
    kind = fd['kind']
    if kind in ('enum', 'bool'):
        s = '; '.join(f'`{v}`={l}' for v, l in sorted(fd['values'].items()))
        if fd.get('menu'):
            s += f' (порядок пунктов меню, №{fd["menu"]["material"]})'
        return s
    if kind == 'num':
        k, unit = fd['scale']
        return f'× {fmt_scale(k)} {unit}'.strip() if k != 1 else f'число, {unit}'
    if kind == 'time6':
        return '`YY MM DD HH MM SS`'
    return ''


def status_cell(fd):
    parts = [f'{fd["status"]} — шаги {steps_ref(fd["steps"])}; {mats_ref(fd)}']
    if fd.get('note'):
        parts.append(fd['note'])
    return '; '.join(parts)


def pos_st(s):
    typ = {1: 'u8', 2: 'u16LE', 4: 'u32LE'}.get(s['size'], f"{s['size']} байт")
    rng = f'{s["off"]}' if s['size'] == 1 else f'{s["off"]}..{s["off"] + s["size"] - 1}'
    return f'{rng} ({typ})'


def pos_cmd(c):
    rng = f'{c["byte"]}' if c['size'] == 1 else f'{c["byte"]}..{c["byte"] + c["size"] - 1} (u16LE)'
    if c.get('mask'):
        rng += f', бит `0x{c["mask"]:02x}`'
    return rng


def rel_text(fd):
    rel = fd.get('rel', 'eq')
    if rel == 'eq':
        return ''
    if isinstance(rel, tuple) and rel[0] == 'mul':
        return f' (статус = байт × {rel[1]})'
    return ' (по правилу, см. кодирование)'


def table_status(obj):
    rows = ['| Смещение | Поле | Кодирование | Команда | Статус |', '|---|---|---|---|---|']
    for fd in sorted([f for f in F.FIELDS if f['st']['obj'] == obj], key=lambda f: f['st']['off']):
        c = fd.get('cmd')
        cref = f'`a1/{c["obj"]:02x}` [{pos_cmd(c)}]{rel_text(fd)}' if c else '—'
        rows.append(f'| {pos_st(fd["st"])} | {fd["name"]} | {encoding(fd)} | {cref} | {status_cell(fd)} |')
    return NL.join(rows)


def table_cmd(obj):
    rows = ['| Байт(ы) | Поле | Кодирование | Статус (отражение) | Статус |', '|---|---|---|---|---|']
    fs = [f for f in F.FIELDS if f.get('cmd') and f['cmd']['obj'] == obj]
    for fd in sorted(fs, key=lambda f: (f['cmd']['byte'], f['cmd'].get('mask', 0))):
        s = fd['st']
        sref = f'`a3/{s["obj"]:02x}` off{s["off"]}{rel_text(fd)}'
        rows.append(f'| {pos_cmd(fd["cmd"])} | {fd["name"]} | {encoding(fd)} | {sref} | {status_cell(fd)} |')
    return NL.join(rows)


def unknown_ranges(obj, length):
    cov = set()
    for fd in F.FIELDS:
        st = fd['st']
        if st['obj'] == obj:
            cov |= set(range(st['off'], st['off'] + st['size']))
    rng = []; i = 0
    while i < length:
        if i in cov:
            i += 1; continue
        j = i
        while j + 1 < length and j + 1 not in cov:
            j += 1
        rng.append(f'{i}' if i == j else f'{i}..{j}')
        i = j + 1
    n = length - len(cov)
    return f'**Неразобранные смещения** ({n} из {length} байт): ' + ', '.join(rng) + ' — побайтово в `OBJECTS.md`.'


def table_commands():
    rows = ['| Код | Полезная нагрузка | Назначение | Статус |', '|---|---|---|---|']
    for cm in sorted(F.COMMANDS, key=lambda c: c['obj']):
        st = cm['status'] + (f' — шаги {steps_ref(cm["steps"])}' if cm['steps'] else '')
        if cm.get('note'):
            st += '; ' + cm['note']
        rows.append(f'| `0x{cm["obj"]:02X}` | {cm["payload"]} | {cm["purpose"]} | {st} |')
    return NL.join(rows)


_FRAMES = None


def window_frames():
    global _FRAMES
    if _FRAMES is None:
        import verify_fields as V
        frames, _ = V.load_frames([])
        w0 = datetime.datetime(*F.WINDOW_START)
        _FRAMES = [(ts, k, f) for ts, k, f in frames if V.local_dt(ts) >= w0]
    return _FRAMES


def objects_table(obj, idx):
    """Побайтовая карта объекта a3/obj по кадрам окна; idx — показываемая запись."""
    import object_map as OM
    fs = [f for ts, k, f in window_frames() if k == 'ANS' and len(f) > 8 and f[3] == 0xA3 and f[4] == obj]
    idxs = sorted({f[5] for f in fs})
    pls = [f[6:-2] for f in fs if f[5] == idx]
    L = min(len(p) for p in pls)
    var = {o for o in range(L) if len({p[o] for p in pls}) > 1}
    b = dict(pls=pls, sample=pls[-1][:L], var=var, known=OM.known_for(0xA3, obj), L=L, idxs=idxs)
    note = f', показана запись idx{idx:02x}' if len(idxs) > 1 else ''
    head = f'Кадров записи в окне: {len(pls)}{note}; пример — последний кадр; C/V — по всем кадрам записи.'
    return OM.md(0xA3, obj, b).replace('\n', NL) + NL + NL + head


def research_objects():
    lines = []
    for obj, title, length, sec in ((0x00, 'основной статус', 88, '§4.1'), (0x0C, 'краткий статус', 20, '§4.2'),
                                    (0x21, 'журнал болюсов (одна запись)', 14, '§4.4')):
        fs = [f for f in F.FIELDS if f['st']['obj'] == obj]
        cov = set()
        for f in fs:
            cov |= set(range(f['st']['off'], f['st']['off'] + f['st']['size']))
        green = [f for f in fs if f['status'] == '🟢']
        yellow = [f for f in fs if f['status'] != '🟢']
        s = (f'- `a3/{obj:02x}` — {title}: разобрано {len(cov)} из {length} байт; полей 🟢 {len(green)}, '
             f'🟡 {len(yellow)}')
        if yellow:
            s += ' (' + ', '.join(f['name'] + f' — off{f["st"]["off"]}' for f in yellow) + ')'
        lines.append(s + f'. Таблица — PROTOCOL.md {sec}.')
    return NL.join(lines)


def research_commands():
    lines = []
    for cm in sorted(F.COMMANDS, key=lambda c: c['obj']):
        st = cm['status'] + (f' (шаги {steps_ref(cm["steps"])})' if cm['steps'] else '')
        nf = [f for f in F.FIELDS if f.get('cmd') and f['cmd']['obj'] == cm['obj']]
        cnt = sum(1 for ts, k, f in window_frames() if k == 'CMD' and f[3] == 0xA1 and f[4] == cm['obj'])
        extra = f'; в окне команд: {cnt}' + (f'; полей в реестре: {len(nf)}' if nf else '')
        lines.append(f'- `a1/{cm["obj"]:02x}` — {cm["purpose"]} — {st}{extra}.')
    return NL.join(lines)


def render(name):
    return {
        'commands': table_commands,
        'a3_00': lambda: table_status(0x00),
        'a3_0c': lambda: table_status(0x0C),
        'a3_21': lambda: table_status(0x21),
        'a3_00_unknown': lambda: unknown_ranges(0x00, 88),
        'a3_0c_unknown': lambda: unknown_ranges(0x0C, 20),
        'a1_32': lambda: table_cmd(0x32),
        'a1_34': lambda: table_cmd(0x34),
        'a1_11': lambda: table_cmd(0x11),
        'a1_02': lambda: table_cmd(0x02),
        'obj_a3_00': lambda: objects_table(0x00, 0xAA),
        'obj_a3_0c': lambda: objects_table(0x0C, 0xAA),
        'obj_a3_31': lambda: objects_table(0x31, 0x00),
        'obj_a3_0a': lambda: objects_table(0x0A, 0x00),
        'obj_a3_0b': lambda: objects_table(0x0B, 0x00),
        'obj_a3_08': lambda: objects_table(0x08, 0x00),
        'obj_a3_07': lambda: objects_table(0x07, 0xAA),
        'obj_a3_21': lambda: objects_table(0x21, 0x00),
        'obj_a3_26': lambda: objects_table(0x26, 0x00),
        'research_objects': research_objects,
        'research_commands': research_commands,
    }[name]()


def process(path, check):
    s = open(path, encoding='utf-8', newline='').read()
    pat = re.compile(r'(<!-- gen:(\w+) -->\r?\n)(.*?)(\r?\n<!-- /gen:\2 -->)', re.S)
    changed = []

    def sub(m):
        new = render(m.group(2))
        if new != m.group(3):
            changed.append(m.group(2))
        return m.group(1) + new + m.group(4)

    out = pat.sub(sub, s)
    if changed and not check:
        open(path, 'w', encoding='utf-8', newline='').write(out)
    return changed


if __name__ == '__main__':
    check = '--check' in sys.argv
    bad = False
    for doc in ('PROTOCOL.md', 'OBJECTS.md', 'RESEARCH.md'):
        ch = process(os.path.join(ROOT, doc), check)
        print(f'{doc}: ' + (('расходятся с реестром: ' if check else 'обновлены: ') + ', '.join(ch) if ch else 'совпадают с реестром'))
        bad |= bool(ch)
    sys.exit(1 if (check and bad) else 0)
