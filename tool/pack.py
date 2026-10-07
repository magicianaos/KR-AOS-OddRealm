import struct, unityser as u

def write_serialized(sf, datas):
    """datas: list aligned with sf.objects (bytes). Returns new serialized file bytes."""
    d=bytearray(sf.data[:sf.data_offset])
    ef = "<" if not sf.big else ">"
    out=bytearray()
    for o,nd in zip(sf.objects, datas):
        while len(out)%16: out.append(0)
        start=len(out); out+=nd
        # patch entry: pathid(8) then byteStart(i64) byteSize(u32) typeid(i32)  [v22]
        eo=o['entry_off']+8
        struct.pack_into(ef+"q",d,eo,start)
        struct.pack_into(ef+"I",d,eo+8,len(nd))
    total=len(d)+len(out)
    struct.pack_into(">q",d,24,total)   # file_size
    return bytes(d)+bytes(out)

def lz4_literals(src):
    out=bytearray(); n=len(src)
    if n<15: out.append(n<<4)
    else:
        out.append(0xF0); r=n-15
        while r>=255: out.append(255); r-=255
        out.append(r)
    out+=src
    return bytes(out)

def write_bundle(nodes, ver=8, unity_ver="5.x.x", unity_rev="6000.4.4f1", flags=0x243, block_flag=0x40):
    """Rebuild a UnityFS archive mimicking the original layout: single uncompressed block."""
    blob=bytearray(); node_recs=[]
    for nm,data in nodes:
        node_recs.append((len(blob), len(data), 4, nm)); blob+=data
    while len(blob)%16: blob.append(0)
    bi=bytearray()
    bi+=b"\0"*16
    bi+=struct.pack(">i",1)
    bi+=struct.pack(">IIH",len(blob),len(blob),block_flag)
    bi+=struct.pack(">i",len(node_recs))
    for off,sz,fl,nm in node_recs:
        bi+=struct.pack(">qqI",off,sz,fl)+nm.encode()+b"\0"
    comp=flags&0x3f
    hdrlen=8+4+len(unity_ver)+1+len(unity_rev)+1+8+12
    if ver>=7: hdrlen=(hdrlen+15)//16*16
    if comp in (2,3):
        cbi=lz4_compress(bytes(bi))
    elif comp==0:
        cbi=bytes(bi)
    else: raise Exception("unsupported blocksInfo compression %d"%comp)
    hdr=bytearray()
    hdr+=b"UnityFS\0"
    hdr+=struct.pack(">i",ver)
    hdr+=unity_ver.encode()+b"\0"
    hdr+=unity_rev.encode()+b"\0"
    size_pos=len(hdr); hdr+=struct.pack(">q",0)
    hdr+=struct.pack(">III",len(cbi),len(bi),flags)
    if ver>=7:
        while len(hdr)%16: hdr.append(0)
    body=bytearray(cbi)
    if flags & 0x200:
        while (len(hdr)+len(body))%16: body.append(0)
    total=len(hdr)+len(body)+len(blob)
    struct.pack_into(">q",hdr,size_pos,total)
    return bytes(hdr)+bytes(body)+bytes(blob)

def lz4_compress(src):
    """Minimal but spec-correct LZ4 block compressor (greedy)."""
    n=len(src)
    if n<13: return lz4_literals(src)
    MINMATCH=4; MFLIMIT=12; LASTLITERALS=5
    table={}
    out=bytearray()
    anchor=0; ip=0
    limit=n-MFLIMIT
    def emit_len(val, out):
        while val>=255: out.append(255); val-=255
        out.append(val)
    while ip < limit:
        seq=src[ip:ip+4]
        cand=table.get(seq)
        table[seq]=ip
        if cand is None or ip-cand>65535 or src[cand:cand+4]!=seq:
            ip+=1; continue
        # extend match
        m=4
        while ip+m<limit+MFLIMIT-LASTLITERALS and src[cand+m:cand+m+1]==src[ip+m:ip+m+1]:
            m+=1
        litlen=ip-anchor
        token_pos=len(out)
        tok=(15 if litlen>=15 else litlen)<<4
        out.append(0)
        if litlen>=15: emit_len(litlen-15,out)
        out+=src[anchor:ip]
        off=ip-cand
        out.append(off & 0xff); out.append((off>>8)&0xff)
        ml=m-MINMATCH
        tok |= (15 if ml>=15 else ml)
        if ml>=15: emit_len(ml-15,out)
        out[token_pos]=tok
        ip+=m; anchor=ip
        for k in range(max(0,ip-m+1), ip):
            if k+4<=n: table[src[k:k+4]]=k
    litlen=n-anchor
    tok=(15 if litlen>=15 else litlen)<<4
    out.append(tok)
    if litlen>=15: emit_len(litlen-15,out)
    out+=src[anchor:]
    return bytes(out)
