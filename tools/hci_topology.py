#!/usr/bin/env python3
"""Разбор btsnoop-захвата и извлечение топологии GATT для каждого BLE-подключения.

Свой парсер проекта: читает btsnoop, собирает L2CAP-фрагменты, разбирает ATT и печатает по
каждому подключению: адрес пира, обмен MTU, службы, характеристики, дескрипторы, записи в CCCD,
уведомления. Идентификационные данные показываются только для анализа; в документы проекта они
не переносятся.
"""
import struct, sys

def uuid_str(b):
    if len(b)==2: return f"0x{b[1]:02X}{b[0]:02X}"
    if len(b)==16:
        r=b[::-1]
        return "-".join(r[i:j].hex() for i,j in [(0,4),(4,6),(6,8),(8,10),(10,16)])
    return b.hex()

def parse(path):
    d=open(path,'rb').read()
    assert d[:8]==b'btsnoop\x00', "не btsnoop"
    ver,dl=struct.unpack('>II',d[8:16])
    off=16
    conns={}          # handle -> dict
    reasm={}          # handle -> [need_len, bytearray]
    t0=None
    def C(h):
        return conns.setdefault(h,{'addr':None,'atype':None,'mtu_req':None,'mtu_rsp':None,
            'services':[], 'chars':[], 'descs':[], 'cccd_writes':[], 'notif':{}, 'pending':None})
    while off+24<=len(d):
        ol,il,fl,drp=struct.unpack('>IIII',d[off:off+16])
        ts,=struct.unpack('>q',d[off+16:off+24])
        off+=24
        pkt=d[off:off+il]; off+=il
        if t0 is None: t0=ts
        recv=fl&1
        if dl==1002:
            if not pkt: continue
            h4=pkt[0]; body=pkt[1:]
        else:
            h4=0x02; body=pkt
        if h4==0x04:  # HCI event
            if len(body)<2: continue
            ev,plen=body[0],body[1]; p=body[2:2+plen]
            if ev==0x3E and p:  # LE meta
                sub=p[0]
                if sub in (0x01,0x0A) and len(p)>=9:
                    status=p[1]; chandle=struct.unpack('<H',p[2:4])[0]; role=p[4]
                    atype=p[5]; addr=p[6:12][::-1]
                    if status==0:
                        c=C(chandle); c['addr']=addr.hex(':'); c['atype']=atype
            continue
        if h4!=0x02:  # только ACL интересен
            continue
        if len(body)<4: continue
        hf,dlen=struct.unpack('<HH',body[:4]); handle=hf&0x0FFF; pb=(hf>>12)&0x3
        payload=body[4:4+dlen]
        if pb==0x02 or pb==0x00:  # start of L2CAP pdu (first fragment)
            if len(payload)<4:
                reasm[handle]=[None,bytearray(payload)]; continue
            l2len,cid=struct.unpack('<HH',payload[:4])
            buf=bytearray(payload)
            need=4+l2len
            if len(buf)>=need:
                handle_att(C(handle),cid,bytes(buf[4:need]),recv)
                reasm.pop(handle,None)
            else:
                reasm[handle]=[need,buf]
        elif pb==0x01:  # continuation
            if handle in reasm and reasm[handle][0] is not None:
                reasm[handle][1]+=payload
                need,buf=reasm[handle]
                if len(buf)>=need:
                    l2len,cid=struct.unpack('<HH',buf[:4])
                    handle_att(C(handle),cid,bytes(buf[4:need]),recv)
                    reasm.pop(handle,None)
    return conns

def handle_att(c,cid,att,recv):
    if cid!=0x0004 or not att: return
    op=att[0]; b=att[1:]
    if op==0x02 and len(b)>=2: c['mtu_req']=struct.unpack('<H',b[:2])[0]
    elif op==0x03 and len(b)>=2: c['mtu_rsp']=struct.unpack('<H',b[:2])[0]
    elif op==0x10 and len(b)>=6: c['pending']=('svc',)          # read by group type req (services)
    elif op==0x08 and len(b)>=6:
        u=uuid_str(b[4:]); c['pending']=('char' if u=='0x2803' else 'byt',u)
    elif op==0x04: c['pending']=('desc',)
    elif op==0x11:  # read by group type rsp -> services
        ln=b[0]; data=b[1:]
        for i in range(0,len(data)-ln+1,ln):
            e=data[i:i+ln]; sh,eh=struct.unpack('<HH',e[:4]); u=uuid_str(e[4:ln])
            c['services'].append((sh,eh,u))
    elif op==0x09:  # read by type rsp
        ln=b[0]; data=b[1:]
        pend=c.get('pending')
        for i in range(0,len(data)-ln+1,ln):
            e=data[i:i+ln]; h=struct.unpack('<H',e[:2])[0]; val=e[2:ln]
            if pend and pend[0]=='char' and len(val)>=3:
                props=val[0]; vh=struct.unpack('<H',val[1:3])[0]; u=uuid_str(val[3:])
                c['chars'].append((h,props,vh,u))
    elif op==0x05:  # find info rsp -> descriptors
        fmt=b[0]; data=b[1:]; step=4 if fmt==1 else 18
        for i in range(0,len(data)-step+1,step):
            h=struct.unpack('<H',data[i:i+2])[0]; u=uuid_str(data[i+2:i+step])
            c['descs'].append((h,u))
    elif op in (0x12,0x52) and len(b)>=2:  # write req / write cmd
        h=struct.unpack('<H',b[:2])[0]; val=b[2:]
        # интересны короткие записи (CCCD 01 00 / 02 00)
        if len(val)<=2:
            c['cccd_writes'].append((h,val.hex(),'->pump' if not recv else '<-pump'))
    elif op==0x1B and len(b)>=2:  # notification
        h=struct.unpack('<H',b[:2])[0]; c['notif'][h]=c['notif'].get(h,0)+1

if __name__=='__main__':
    conns=parse(sys.argv[1])
    for h,c in conns.items():
        if not (c['services'] or c['chars'] or c['mtu_rsp'] or c['notif']): continue
        print(f"\n=== conn handle 0x{h:04X}  peer={c['addr']} (type {c['atype']}) ===")
        print(f"  MTU: req={c['mtu_req']} rsp={c['mtu_rsp']}")
        print(f"  Службы ({len(c['services'])}):")
        for s in c['services']: print(f"    {s[2]:20s} handles 0x{s[0]:04X}-0x{s[1]:04X}")
        print(f"  Характеристики ({len(c['chars'])}):")
        for ch in c['chars']:
            props=ch[1]; fl=[]
            for bit,name in [(0x02,'READ'),(0x04,'WRITE_NR'),(0x08,'WRITE'),(0x10,'NOTIFY'),(0x20,'INDICATE')]:
                if props&bit: fl.append(name)
            print(f"    {ch[3]:20s} decl 0x{ch[0]:04X} value 0x{ch[2]:04X} props 0x{props:02X} [{'|'.join(fl)}]")
        if c['descs']:
            print(f"  Дескрипторы ({len(c['descs'])}):")
            for dsc in c['descs']:
                if dsc[1] in ('0x2902','0x2803','0x2800'): print(f"    {dsc[1]} @0x{dsc[0]:04X}")
        if c['cccd_writes']:
            print("  Короткие записи (вкл. CCCD):")
            for w in c['cccd_writes'][:10]: print(f"    @0x{w[0]:04X} = {w[1]} {w[2]}")
        if c['notif']:
            print("  Уведомления по handle:", {f"0x{k:04X}":v for k,v in c['notif'].items()})
