#!/usr/bin/env python3
"""Выделение периодического кадра-«пульса» помпы (класс 0xA5) из btsnoop: печатает метку времени,
интервал между кадрами, длину, полезную нагрузку и проверку CRC-16/MODBUS. Позволяет оценить
периодичность и постоянство heartbeat. Идентификаторов в этих кадрах нет.
"""
import struct, sys, datetime
ANS=0x001C; EPOCH=62167219200000000
def hms(ts): return (datetime.datetime(1970,1,1)+datetime.timedelta(microseconds=ts-EPOCH)).strftime("%H:%M:%S")
def modbus(data):
    crc=0xFFFF
    for x in data:
        crc^=x
        for _ in range(8): crc=(crc>>1)^0xA001 if crc&1 else crc>>1
    return bytes([crc&0xff,crc>>8])
def scan(path):
    d=open(path,'rb').read(); dl=struct.unpack('>I',d[12:16])[0]; off=16; out=[]
    while off+24<=len(d):
        il=struct.unpack('>I',d[off+4:off+8])[0]; ts=struct.unpack('>q',d[off+16:off+24])[0]; off+=24
        pkt=d[off:off+il]; off+=il
        if dl==1002:
            if not pkt: continue
            h4=pkt[0]; body=pkt[1:]
        else: h4=0x02; body=pkt
        if h4!=0x02 or len(body)<4: continue
        hf,dlen=struct.unpack('<HH',body[:4]); handle=hf&0x0FFF; pb=(hf>>12)&0x3
        payload=body[4:4+dlen]
        if pb in (0,2) and len(payload)>=4:
            l2len,cid=struct.unpack('<HH',payload[:4])
            if cid==0x0004:
                att=payload[4:4+l2len]
                if att and att[0]==0x1B and len(att)>=3 and struct.unpack('<H',att[1:3])[0]==ANS:
                    v=att[3:]
                    if len(v)>=4 and v[0]==0xAA and v[3]==0xA5: out.append((ts,v))
    return out
if __name__=='__main__':
    n=scan(sys.argv[1]); prev=None
    print(f"# кадров a5: {len(n)}")
    for ts,v in n:
        dt=f"+{(ts-prev)/1e6:6.1f}s" if prev else "   ---  "
        ok = v[-2:]==modbus(v[:-2])
        print(f"{hms(ts)} {dt} len={len(v)} crc={'ok' if ok else 'no'} {v.hex()}")
        prev=ts
