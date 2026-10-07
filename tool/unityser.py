import struct, io, sys

class R:
    def __init__(self, d, big=True):
        self.d=d; self.p=0; self.big=big
    def _f(self,c): return (">" if self.big else "<")+c
    def u8(self):
        v=self.d[self.p]; self.p+=1; return v
    def i16(self):
        v=struct.unpack_from(self._f("h"),self.d,self.p)[0]; self.p+=2; return v
    def u16(self):
        v=struct.unpack_from(self._f("H"),self.d,self.p)[0]; self.p+=2; return v
    def i32(self):
        v=struct.unpack_from(self._f("i"),self.d,self.p)[0]; self.p+=4; return v
    def u32(self):
        v=struct.unpack_from(self._f("I"),self.d,self.p)[0]; self.p+=4; return v
    def i64(self):
        v=struct.unpack_from(self._f("q"),self.d,self.p)[0]; self.p+=8; return v
    def u64(self):
        v=struct.unpack_from(self._f("Q"),self.d,self.p)[0]; self.p+=8; return v
    def cstr(self):
        e=self.d.index(b"\0",self.p); s=self.d[self.p:e].decode("utf8","replace"); self.p=e+1; return s
    def raw(self,n):
        v=self.d[self.p:self.p+n]; self.p+=n; return v
    def align(self,n=4):
        self.p=(self.p+n-1)//n*n

class SerializedFile:
    def __init__(self, data):
        self.data=data
        r=R(data,True)
        metadata_size=r.u32(); file_size=r.u32(); self.version=r.u32(); data_offset=r.u32()
        if self.version>=9:
            endian=r.u8(); r.raw(3)
        else:
            endian=1
        if self.version>=22:
            metadata_size=r.u32(); file_size=r.u64(); data_offset=r.u64(); r.u64()
        big = endian==1
        r.big=big
        self.big=big
        self.unity_version=r.cstr()
        self.target_platform=r.i32()
        self.enable_typetree = r.u8()!=0 if self.version>=13 else True
        type_count=r.i32()
        self.types=[]
        for _ in range(type_count):
            self.types.append(self._read_type(r, False))
        obj_count=r.i32()
        self.objects=[]
        for _ in range(obj_count):
            r.align(4)
            entry_off=r.p
            path_id=r.i64()
            if self.version>=22:
                byte_start=r.i64(); byte_size=r.u32(); type_id=r.i32()
            else:
                byte_start=r.u32(); byte_size=r.u32(); type_id=r.i32()
            self.objects.append(dict(entry_off=entry_off, path_id=path_id, start=byte_start+data_offset,
                                     size=byte_size, type_id=type_id,
                                     class_id=self.types[type_id]["class_id"],
                                     script_index=self.types[type_id].get("script_index")))
        self.data_offset=data_offset
        self.metadata_size=metadata_size
        self.header_end=r.p

    def _read_type(self, r, is_ref):
        t={}
        t["class_id"]=r.i32()
        if self.version>=16: t["stripped"]=r.u8()
        if self.version>=17: t["script_index"]=r.i16()
        if self.version>=13:
            if (self.version<16 and t["class_id"]<0) or (self.version>=16 and t["class_id"]==114):
                t["script_hash"]=r.raw(16)
            t["type_hash"]=r.raw(16)
        if self.enable_typetree:
            import tt
            root, nodes = tt.parse_typetree(r, self.version)
            t["root"]=root; t["nodes"]=nodes
            if self.version>=21:
                if is_ref:
                    t["klass"]=r.cstr(); t["ns"]=r.cstr(); t["asm"]=r.cstr()
                else:
                    n=r.i32(); t["deps"]=[r.i32() for _ in range(n)]
        return t

    def obj_data(self, o):
        return self.data[o["start"]:o["start"]+o["size"]]

def read_bundle(path):
    """returns list of (name, data) for files inside a UnityFS bundle"""
    d=open(path,'rb').read()
    r=R(d,True)
    sig=r.cstr()
    assert sig=="UnityFS", sig
    ver=r.u32(); r.cstr(); r.cstr()
    size=r.i64()
    cbis=r.u32(); ubis=r.u32(); flags=r.u32()
    if ver>=7: r.align(16)
    if flags & 0x80:
        save=r.p
        blk=d[size-cbis:size]
    else:
        blk=r.raw(cbis)
        if flags & 0x200: r.align(16)
    comp=flags&0x3f
    bi=decompress(blk, comp, ubis)
    br=R(bi,True)
    br.raw(16)
    nblocks=br.i32()
    blocks=[]
    for _ in range(nblocks):
        u=br.u32(); c=br.u32(); f=br.u16(); blocks.append((u,c,f))
    nnodes=br.i32()
    nodes=[]
    for _ in range(nnodes):
        off=br.i64(); sz=br.i64(); fl=br.u32(); nm=br.cstr(); nodes.append((off,sz,fl,nm))
    if flags & 0x80:
        r.p=save
    out=bytearray()
    for (u,c,f) in blocks:
        chunk=r.raw(c)
        out+=decompress(chunk, f&0x3f, u)
    res=[]
    for off,sz,fl,nm in nodes:
        res.append((nm, bytes(out[off:off+sz])))
    return res

def decompress(data, comp, usize):
    if comp==0: return data
    if comp in (2,3): return lz4_block(data, usize)
    if comp==1:
        import lzma
        props=data[:5]
        dec=lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[lzma._decode_filter_properties(lzma.FILTER_LZMA1, props)])
        return dec.decompress(data[5:], usize)
    raise Exception("comp %d"%comp)

def lz4_block(src, usize):
    dst=bytearray()
    i=0; n=len(src)
    while i<n:
        tok=src[i]; i+=1
        lit=tok>>4
        if lit==15:
            while True:
                b=src[i]; i+=1; lit+=b
                if b!=255: break
        dst+=src[i:i+lit]; i+=lit
        if i>=n: break
        off=src[i] | (src[i+1]<<8); i+=2
        ml=tok&0xf
        if ml==15:
            while True:
                b=src[i]; i+=1; ml+=b
                if b!=255: break
        ml+=4
        start=len(dst)-off
        for k in range(ml):
            dst.append(dst[start+k])
    return bytes(dst)
