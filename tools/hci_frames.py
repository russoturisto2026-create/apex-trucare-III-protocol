#!/usr/bin/env python3
"""Сбор прикладных кадров помпы из btsnoop: команды (запись в 0x0021) и ответы
(уведомления 0x001C), с реассемблированием ответа по полю длины (байт [1]) через несколько
уведомлений, и проверкой CRC-16/MODBUS (little-endian) последних двух байт.

Идентификационный блок команд ("APEX"+серийный номер) при печати заменяется на <identity>.
"""
import struct, sys, re
CMD=0x0021; ANS=0x001C

def _modbus(data):
    crc=0xFFFF
    for x in data:
        crc^=x
        for _ in range(8): crc=(crc>>1)^0xA001 if crc&1 else crc>>1
    return bytes([crc&0xff, crc>>8])

BTSNOOP_EPOCH_US=0x00DCDDB30F2F8000  # микросекунды от 0000-01-01 до 1970-01-01 (формат btsnoop)

def _events(src):
    d=src if isinstance(src,(bytes,bytearray)) else open(src,'rb').read(); assert d[:8]==b'btsnoop\x00'
    dl=struct.unpack('>I',d[12:16])[0]; off=16; reasm={}; ev=[]
    while off+24<=len(d):
        il=struct.unpack('>I',d[off+4:off+8])[0]; fl=struct.unpack('>I',d[off+8:off+12])[0]
        ts=(struct.unpack('>q',d[off+16:off+24])[0]-BTSNOOP_EPOCH_US)/1e6  # местное время телефона как «наивный» unix-ts (Android пишет local time)
        off+=24; pkt=d[off:off+il]; off+=il; recv=fl&1
        if dl==1002:
            if not pkt: continue
            h4=pkt[0]; body=pkt[1:]
        else: h4=0x02; body=pkt
        if h4!=0x02 or len(body)<4: continue
        hf,dlen=struct.unpack('<HH',body[:4]); handle=hf&0x0FFF; pb=(hf>>12)&0x3
        payload=body[4:4+dlen]
        if pb in (0,2):
            if len(payload)<4: reasm[handle]=[None,bytearray(payload)]; continue
            l2len,cid=struct.unpack('<HH',payload[:4]); need=4+l2len; buf=bytearray(payload)
            if len(buf)>=need: _a(ev,bytes(buf[4:need]),recv,ts); reasm.pop(handle,None)
            else: reasm[handle]=[need,buf,cid]
        elif pb==1 and handle in reasm and reasm[handle][0] is not None:
            reasm[handle][1]+=payload; need,buf,cid=reasm[handle]
            if len(buf)>=need: _a(ev,bytes(buf[4:need]),recv,ts); reasm.pop(handle,None)
    return ev
def _a(ev,att,recv,ts=None):
    if not att: return
    op=att[0]; b=att[1:]
    if op in (0x12,0x52) and len(b)>=2 and struct.unpack('<H',b[:2])[0]==CMD: ev.append(('CMD',b[2:],ts))
    elif op==0x1B and len(b)>=2 and struct.unpack('<H',b[:2])[0]==ANS: ev.append(('ANS',b[2:],ts))

def frames(path):
    """Логические кадры: команды как есть; ответы реассемблируются по длине [1]."""
    return [(k,f) for k,f,_ in frames_ts(path)]

def frames_ts(src):
    """То же, что frames(), но с меткой времени btsnoop третьим элементом (местное время телефона в виде
    «наивного» unix-времени: datetime.utcfromtimestamp даёт часы телефона).
    src — путь к файлу или содержимое btsnoop (bytes)."""
    out=[]; buf=bytearray()
    for kind,val,ts in _events(src):
        if kind=='CMD': out.append(('CMD',bytes(val),ts)); continue
        buf+=val
        while len(buf)>=2 and buf[0]==0xAA:
            ln=buf[1]
            if ln<4 or len(buf)<ln: break
            out.append(('ANS',bytes(buf[:ln]),ts)); del buf[:ln]
        if buf and buf[0]!=0xAA: buf=bytearray()  # сброс мусора
    return out

def sanitize(hexstr):
    # заменяем идентификационный блок ASCII "APEX"(41504558)+8 байт серийника на плейсхолдер,
    # не сохраняя само значение серийника в коде
    return re.sub(r'41504558[0-9a-f]{16}', '<identity>', hexstr)

if __name__=='__main__':
    n_ok=n_bad=0
    for kind,f in frames(sys.argv[1]):
        crc_ok = f[-2:]==_modbus(f[:-2]) if len(f)>=4 else False
        n_ok+=crc_ok; n_bad+= (not crc_ok)
        if len(sys.argv)>2 and sys.argv[2]=='-v':
            print(f"{kind} len={len(f):3d} crc={'ok' if crc_ok else 'BAD'} cls={f[3]:02x} obj={f[4]:02x} idx={f[5]:02x} {sanitize(f.hex())}")
    print(f"# кадров с верным CRC: {n_ok}, с неверным: {n_bad}")
