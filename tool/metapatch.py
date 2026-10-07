import orpaths
import numpy as np, struct, json, glob, os

SRC=orpaths.src('metadata')
OUT=orpaths.out('patch_meta','global-metadata.dat')
TBL_OFF_POS, TBL_SIZE_POS, TBL_CNT_POS = 8, 12, 16
DAT_OFF_POS, DAT_SIZE_POS, DAT_CNT_POS = 20, 24, 28

def main():
    d=bytearray(open(SRC,'rb').read())
    TBL=struct.unpack_from('<i',d,TBL_OFF_POS)[0]
    TSZ=struct.unpack_from('<i',d,TBL_SIZE_POS)[0]
    NOFF=struct.unpack_from('<i',d,TBL_CNT_POS)[0]
    DOFF=struct.unpack_from('<i',d,DAT_OFF_POS)[0]
    DSZ=struct.unpack_from('<i',d,DAT_SIZE_POS)[0]
    NLIT=struct.unpack_from('<i',d,DAT_CNT_POS)[0]
    assert NOFF*4==TSZ and NLIT==NOFF-1, (NOFF,TSZ,NLIT)
    off=np.frombuffer(bytes(d[TBL:TBL+TSZ]),dtype='<i4')
    assert off[-1]==DSZ
    lits=[bytes(d[DOFF+off[k]:DOFF+off[k+1]]) for k in range(NLIT)]

    M={}
    for f in sorted(glob.glob(os.path.join(orpaths.TOOL,'tr','meta','*.json'))):
        M.update(json.load(open(f)))
    hit=0; new=[]
    for s in lits:
        try: t=s.decode('utf8')
        except Exception: new.append(s); continue
        if t in M:
            new.append(M[t].encode('utf8')); hit+=1
        else:
            new.append(s)
    print('translated literals:', hit, 'of', len(M), 'map entries')
    missing=[k for k in M if k.encode('utf8') not in lits]
    if missing: print('WARNING not found in metadata:', missing[:10], '...' if len(missing)>10 else '')

    blob=b''.join(new)
    newoff=np.zeros(NOFF,dtype='<i4')
    acc=0
    for i,s in enumerate(new):
        newoff[i]=acc; acc+=len(s)
    newoff[NLIT]=acc
    assert acc==len(blob)

    # place new blob at EOF (16-aligned)
    while len(d)%16: d.append(0)
    NEWDOFF=len(d)
    d+=blob
    d[TBL:TBL+TSZ]=newoff.tobytes()
    struct.pack_into('<i',d,DAT_OFF_POS,NEWDOFF)
    struct.pack_into('<i',d,DAT_SIZE_POS,len(blob))
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    open(OUT,'wb').write(bytes(d))
    print('old size %d -> new %d (blob %d -> %d)'%(os.path.getsize(SRC),len(d),DSZ,len(blob)))
    return OUT

def verify(path):
    d=open(path,'rb').read()
    TBL=struct.unpack_from('<i',d,TBL_OFF_POS)[0]; TSZ=struct.unpack_from('<i',d,TBL_SIZE_POS)[0]
    DOFF=struct.unpack_from('<i',d,DAT_OFF_POS)[0]; DSZ=struct.unpack_from('<i',d,DAT_SIZE_POS)[0]
    NLIT=struct.unpack_from('<i',d,DAT_CNT_POS)[0]
    off=np.frombuffer(d[TBL:TBL+TSZ],dtype='<i4')
    assert off[0]==0 and off[-1]==DSZ and DOFF+DSZ<=len(d)
    assert bool(np.all(off[1:]>=off[:-1]))
    ok=0
    for k in (0,1,100,5000,NLIT-1):
        s=d[DOFF+off[k]:DOFF+off[k+1]]
        ok+=1
    for probe in ('종족 특성:','왕국 생성','정착지 크기','시작 아이템:'):
        assert probe.encode('utf8') in d, probe
    print('verify OK  literals',NLIT,'blob',DSZ,'file',len(d))

if __name__=='__main__':
    verify(main())
