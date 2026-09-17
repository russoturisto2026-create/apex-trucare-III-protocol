#!/usr/bin/env python3
"""Проверка реестра полей (tools/fields.py) по архивным захватам.

Источник данных — все btsnoop-логи внутри archive/**/NN-hci.zip (стенд не нужен); кадры из разных
архивов объединяются без повторов и упорядочиваются по времени. В выводы идут только кадры внутри
окна исследования (fields.WINDOW_START).

Что проверяется для каждого поля:
  СВЯЗЬ     — статус (a3) совпадает с последней командой (a1) по правилу rel; расхождение, не
              исправленное следующим кадром статуса, — ошибка (у полей pump_side — смена на помпе)
  ЗНАЧЕНИЯ  — каждое наблюдённое значение описано; каждое описанное значение enum/bool
              подтверждено эфиром или пунктом меню (со скриншотом)
  МЕНЮ      — подписи значений enum совпадают с пунктами меню по порядку
  ЭКРАН     — сверки с экраном согласуются с описанием значений
  СТАТУС    — 🟢 только при ≥2 разных значениях в окне и хотя бы одном совпадении связи
  ССЫЛКИ    — шаги есть в RESEARCH.md, материалы — в MATERIALS.md
  БИТЫ      — в байтах-битовых полях не встречаются неописанные биты

Использование: verify_fields.py [--verbose] [доп. btsnoop-файлы …]
Код выхода 1 — есть ошибки.
"""
import sys, os, re, glob, zipfile, datetime, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hci_frames as H
import fields as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def local_dt(ts):
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ts)


def load_frames(extra):
    blobs = []
    for z in sorted(glob.glob(os.path.join(ROOT, 'archive', '*', '*-hci.zip'))):
        with zipfile.ZipFile(z) as a:
            for n in a.namelist():
                if n.endswith('.log'):
                    blobs.append((os.path.relpath(z, ROOT) + ':' + n, a.read(n)))
    for p in extra:
        blobs.append((p, open(p, 'rb').read()))
    seen = set(); out = []
    for name, data in blobs:
        if data[:8] != b'btsnoop\x00':
            continue
        for kind, f, ts in H.frames_ts(data):
            key = (round(ts, 6), kind, f)
            if key in seen:
                continue
            seen.add(key); out.append((ts, kind, f))
    out.sort(key=lambda e: e[0])
    return out, len(blobs)


def getv(buf, off, size, mask=None):
    if off + size > len(buf):
        return None
    v = int.from_bytes(buf[off:off + size], 'little')
    if mask:
        v = (v & mask) >> ((mask & -mask).bit_length() - 1)
    return v


def rel_expected(field, cmd_val, cmd_pl, st_pl):
    rel = field.get('rel', 'eq')
    if rel == 'eq':
        return cmd_val
    if isinstance(rel, tuple) and rel[0] == 'mul':
        return cmd_val * rel[1]
    if rel == 'tbr_rate':
        if cmd_pl[0] == 1:
            return cmd_val
        basal = getv(st_pl, 76, 2)
        return basal * cmd_val // 100
    raise ValueError(rel)


def fmt_num(field, raw):
    k, unit = field.get('scale', (1, ''))
    if k is None:
        return str(raw)
    v = raw * k
    s = ('%g' % round(v, 3)).replace('.', ',')
    return f'{s} {unit}'.strip()


def main():
    verbose = '--verbose' in sys.argv
    extra = [a for a in sys.argv[1:] if not a.startswith('--')]
    frames, nlogs = load_frames(extra)
    w0 = datetime.datetime(*F.WINDOW_START)
    research = open(os.path.join(ROOT, 'RESEARCH.md'), encoding='utf-8').read()
    materials = open(os.path.join(ROOT, 'MATERIALS.md'), encoding='utf-8').read()
    steps_have = {int(m) for m in re.findall(r'^### Шаг (\d{3})', research, re.M)}
    mats_have = {int(m) for m in re.findall(r'^\| (\d+) \|', materials, re.M)}
    win = [(ts, k, f) for ts, k, f in frames if local_dt(ts) >= w0]
    print(f'# логов: {nlogs}; кадров: {len(frames)}, в окне (≥{w0:%d.%m %H:%M}): {len(win)}')
    if win:
        print(f'# окно данных: {local_dt(win[0][0]):%d.%m %H:%M} — {local_dt(win[-1][0]):%d.%m %H:%M}')

    errors = warns = 0

    def err(fid, msg):
        nonlocal errors; errors += 1; print(f'  ОШИБКА [{fid}] {msg}')

    def warn(fid, msg):
        nonlocal warns; warns += 1; print(f'  предупр. [{fid}] {msg}')

    for fd in F.FIELDS:
        fid = fd['id']; c = fd.get('cmd'); s = fd['st']; kind = fd['kind']
        obs_cmd, obs_st = set(), set()
        last = None           # (ts, cmd_val, cmd_pl)
        pending = None        # (ts, expected, got)
        n_match = 0; mism = []; pump_changes = []
        for ts, k, f in win:
            if c and k == 'CMD' and len(f) > 18 and f[3] == 0xA1 and f[4] == c['obj']:
                pl = f[18:-2]; v = getv(pl, c['byte'], c['size'], c.get('mask'))
                if v is None:
                    continue
                obs_cmd.add(v); last = (ts, v, pl)
            elif (k == 'ANS' and len(f) > 8 and f[3] == 0xA3 and f[4] == s['obj']
                  and (s.get('records') or f[5] == 0xAA)):
                pl = f[6:-2]; v = getv(pl, s['off'], s['size'], s.get('mask'))
                if v is None:
                    continue
                act = fd.get('active')
                if act and pl[act[0]] != act[1]:
                    continue
                obs_st.add(v)
                if not c or last is None:
                    continue
                exp = rel_expected(fd, last[1], last[2], pl)
                if pending is not None:
                    if v != pending[1]:
                        if fd.get('pump_side') and v == pending[2]:
                            pump_changes.append((pending[0], pending[1], v))
                            last = (last[0], v, last[2]); exp = v
                        else:
                            mism.append(pending)
                    pending = None
                if v == exp:
                    n_match += 1
                else:
                    pending = (ts, exp, v)
        if pending is not None:
            mism.append(pending)

        obs = obs_cmd | obs_st
        print(f'\n[{fid}] {fd["name"]} — {fd["status"]}')
        if c:
            print(f'  команда a1/{c["obj"]:02x}[{c["byte"]}]: {sorted(obs_cmd)}; статус a3/{s["obj"]:02x} off{s["off"]}: '
                  f'{sorted(obs_st) if len(obs_st) < 12 else "%d значений" % len(obs_st)}; совпадений связи: {n_match}')
        else:
            print(f'  статус a3/{s["obj"]:02x} off{s["off"]}: '
                  f'{sorted(obs_st) if len(obs_st) < 12 else "%d значений" % len(obs_st)}')
        for ts, was, now in pump_changes:
            print(f'  смена на помпе в {local_dt(ts):%d.%m %H:%M:%S}: {was} → {now} (без команды приложения)')
        for ts, exp, got in mism:
            err(fid, f'связь нарушена в {local_dt(ts):%d.%m %H:%M:%S}: ожидалось {exp}, в статусе {got}')

        values = fd.get('values'); menu = fd.get('menu')
        if kind in ('enum', 'bool'):
            if c:
                cmd_obs = obs_cmd
                st_as_cmd = set()
                for v in obs_st:
                    rel = fd.get('rel', 'eq')
                    if isinstance(rel, tuple) and rel[0] == 'mul':
                        if v % rel[1]:
                            err(fid, f'значение статуса {v} не кратно {rel[1]}')
                            continue
                        v //= rel[1]
                    st_as_cmd.add(v)
                vals_seen = cmd_obs | st_as_cmd
            else:
                vals_seen = obs_st
            for v in sorted(vals_seen):
                if v not in values:
                    err(fid, f'наблюдалось неописанное значение {v}')
            for v, lbl in values.items():
                in_menu = bool(menu and menu.get('material') and v < len(menu['items']))
                if v not in vals_seen and not in_menu:
                    err(fid, f'значение {v} «{lbl}» описано, но не наблюдалось в окне и не подтверждено меню')
            if menu:
                items = menu['items']
                for i, it in enumerate(items):
                    if values.get(i) != it:
                        err(fid, f'пункт меню #{i} «{it}» ≠ описанию «{values.get(i)}»')
                if menu.get('complete') and len(items) != len(values):
                    err(fid, f'в меню {len(items)} пунктов, описано {len(values)} значений')
            for raw, lbl, mat in fd.get('screens', []):
                if raw not in values:
                    err(fid, f'сверка с экраном (№{mat}): значение {raw} не описано')
                elif not fd['id'].startswith('tbr_') and values[raw] != lbl:
                    err(fid, f'сверка с экраном (№{mat}): для {raw} на экране «{lbl}», в описании «{values[raw]}»')
        elif kind == 'num':
            for raw, lbl, mat in fd.get('screens', []):
                if raw not in obs and mat not in (6, 9):
                    warn(fid, f'значение со скриншота №{mat} ({raw} = «{lbl}») не встретилось в эфире окна')

        distinct = len(obs)
        ok_green = distinct >= 2 and (not c or n_match > 0) and not mism
        if fd['status'] == '🟢' and not ok_green:
            err(fid, f'статус 🟢 без оснований: разных значений в окне {distinct}, совпадений связи {n_match}, расхождений {len(mism)}')
        if fd['status'] == '🟡' and ok_green and verbose:
            print(f'  (данных достаточно для 🟢 по формальному правилу — решение за исследователем)')

        for st in fd.get('steps', []):
            if st not in steps_have:
                err(fid, f'шаг {st:03d} отсутствует в RESEARCH.md')
        for m in fd.get('materials', []) + [x[2] for x in fd.get('screens', [])]:
            if m not in mats_have:
                err(fid, f'материал №{m} отсутствует в MATERIALS.md')

    # неописанные биты в битовых байтах команд
    print('\n[биты] битовые байты команд')
    groups = {}
    for fd in F.FIELDS:
        c = fd.get('cmd')
        if c and c.get('mask'):
            groups.setdefault((c['obj'], c['byte']), 0)
            groups[(c['obj'], c['byte'])] |= c['mask']
    for (obj, byte), mask in sorted(groups.items()):
        extra_bits = 0
        for ts, k, f in win:
            if k == 'CMD' and len(f) > 18 and f[3] == 0xA1 and f[4] == obj:
                v = getv(f[18:-2], byte, 1)
                if v is not None:
                    extra_bits |= v & ~mask
        print(f'  a1/{obj:02x}[{byte}]: описаны биты 0x{mask:02x}; прочие биты в эфире: 0x{extra_bits:02x}')
        if extra_bits:
            err(f'a1/{obj:02x}[{byte}]', f'в эфире встречаются неописанные биты 0x{extra_bits:02x}')

    print('\n[команды] наблюдения в окне')
    for cm in F.COMMANDS:
        cid = f'a1/{cm["obj"]:02x}'
        cnt = sum(1 for ts, k, f in win if k == 'CMD' and len(f) > 5 and f[3] == 0xA1 and f[4] == cm['obj'])
        print(f'  {cid}: {cnt} — {cm["status"]}')
        if cm['status'] == '🟢' and cnt < 2 and not cm.get('screen_check'):
            err(cid, f'статус 🟢 при {cnt} наблюдении(ях) в окне без сверки с экраном (screen_check)')
        for st in cm.get('steps', []):
            if st not in steps_have:
                err(cid, f'шаг {st:03d} отсутствует в RESEARCH.md')

    print(f'\n# итог: ошибок {errors}, предупреждений {warns}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
