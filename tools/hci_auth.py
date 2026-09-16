#!/usr/bin/env python3
"""Таймлайн BLE-соединений и обмена по каналу авторизации помпы (служба 0xFFC0).

Сегментирует захват по событиям LE Connection Complete / Disconnection Complete и для каждого
соединения печатает: обмен MTU, включение уведомлений (CCCD), записи в характеристику
авторизации (value-handle по умолчанию 0x0041) и уведомления-вердикты (0x0044), а также первые
кадры на канале ответов (0x001C). Значение PIN — секрет; здесь показывается только для локального
анализа и в документы проекта не переносится.
"""
import struct, sys, datetime

AUTH_WRITE=0x0041; AUTH_NOTIFY=0x0044; ANSWER=0x001C; CMD_WRITE=0x0021
BTSNOOP_EPOCH=62167219200000000  # мкс между 0000-01-01 и 1970-01-01

def ts_to_hms(ts):
    try:
        return (datetime.datetime(1970,1,1)+datetime.timedelta(microseconds=ts-BTSNOOP_EPOCH)).strftime("%H:%M:%S")
    except Exception:
        return "?"

def parse(path, only=None):
    d=open(path,'rb').read(); assert d[:8]==b'btsnoop\x00'
    ver,dl=struct.unpack('>II',d[8:16]); off=16
    reasm={}
    def emit(handle,ts,cid,att,recv):
        if cid!=0x0004 or not att: return
        op=att[0]; b=att[1:]
        tag=None
        if op==0x02 and len(b)>=2: tag=f"MTU req {struct.unpack('<H',b[:2])[0]}"
        elif op==0x03 and len(b)>=2: tag=f"MTU rsp {struct.unpack('<H',b[:2])[0]}"
        elif op in (0x12,0x52) and len(b)>=2:
            h=struct.unpack('<H',b[:2])[0]; val=b[2:]
            if h==AUTH_WRITE: tag=f"WRITE ->0xFFC1(auth)  len={len(val)}  hex={val.hex()}"
            elif h==CMD_WRITE: tag=f"WRITE ->0xFFE9(cmd)  len={len(val)}  hex={val[:16].hex()}{'..' if len(val)>16 else ''}"
            elif len(val)<=2: tag=f"WRITE ->0x{h:04X}(cccd) {val.hex()}"
        elif op==0x1B and len(b)>=2:
            h=struct.unpack('<H',b[:2])[0]; val=b[2:]
            if h==AUTH_NOTIFY: tag=f"NOTIFY <-0xFFC2(verdict) len={len(val)} hex={val.hex()}"
            elif h==ANSWER: tag=f"NOTIFY <-0xFFE4(answer) len={len(val)} hex={val[:16].hex()}{'..' if len(val)>16 else ''}"
        elif op==0x13: tag="WRITE rsp"
        if tag: print(f"  [{ts_to_hms(ts)}] h0x{handle:04X} {'RX' if recv else 'TX'}  {tag}")
    while off+24<=len(d):
        ol,il,fl,drp=struct.unpack('>IIII',d[off:off+16]); ts,=struct.unpack('>q',d[off+16:off+24]); off+=24
        pkt=d[off:off+il]; off+=il; recv=fl&1
        if dl==1002:
            if not pkt: continue
            h4=pkt[0]; body=pkt[1:]
        else: h4=0x02; body=pkt
        if h4==0x04:
            if len(body)<2: continue
            ev,plen=body[0],body[1]; p=body[2:2+plen]
            if ev==0x05 and len(p)>=4:
                ch=struct.unpack('<H',p[1:3])[0]; print(f"[{ts_to_hms(ts)}] --- DISCONNECT conn 0x{ch:04X} (reason 0x{p[3]:02X}) ---")
            elif ev==0x3E and p and p[0] in (0x01,0x0A) and len(p)>=9:
                st=p[1]; ch=struct.unpack('<H',p[2:4])[0]; addr=p[6:12][::-1].hex(':')
                if st==0: print(f"\n[{ts_to_hms(ts)}] === CONNECT conn 0x{ch:04X} peer {addr} ===")
            continue
        if h4!=0x02 or len(body)<4: continue
        hf,dlen=struct.unpack('<HH',body[:4]); handle=hf&0x0FFF; pb=(hf>>12)&0x3
        payload=body[4:4+dlen]
        if pb in (0x00,0x02):
            if len(payload)<4: reasm[handle]=[None,bytearray(payload),ts]; continue
            l2len,cid=struct.unpack('<HH',payload[:4]); need=4+l2len; buf=bytearray(payload)
            if len(buf)>=need: emit(handle,ts,cid,bytes(buf[4:need]),recv); reasm.pop(handle,None)
            else: reasm[handle]=[need,buf,ts]
        elif pb==0x01 and handle in reasm and reasm[handle][0] is not None:
            reasm[handle][1]+=payload; need,buf,t0=reasm[handle]
            if len(buf)>=need:
                l2len,cid=struct.unpack('<HH',buf[:4]); emit(handle,t0,cid,bytes(buf[4:need]),recv); reasm.pop(handle,None)

if __name__=='__main__':
    parse(sys.argv[1])
