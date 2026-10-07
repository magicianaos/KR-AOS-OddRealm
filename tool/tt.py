import struct
from commonstr import COMMON_STRING

PRIM = {
 "SInt8":("b",1),"UInt8":("B",1),"char":("B",1),"bool":("?",1),
 "SInt16":("h",2),"short":("h",2),"UInt16":("H",2),"unsigned short":("H",2),
 "SInt32":("i",4),"int":("i",4),"UInt32":("I",4),"unsigned int":("I",4),"Type*":("I",4),
 "SInt64":("q",8),"long long":("q",8),"UInt64":("Q",8),"unsigned long long":("Q",8),"FileSize":("Q",8),
 "float":("f",4),"double":("d",8),
}

class Node:
    __slots__=("version","level","flags","type","name","size","index","meta","children")
    def __init__(self): self.children=[]
    def __repr__(self): return f"<{self.type} {self.name} lvl?>"

def parse_typetree(r, sfver):
    n_nodes=r.i32(); strbuf_size=r.i32()
    raw=[]
    for _ in range(n_nodes):
        nd=Node()
        nd.version=r.u16(); nd.level=r.u8(); nd.flags=r.u8()
        toff=r.u32(); noff=r.u32()
        nd.size=r.i32(); nd.index=r.i32(); nd.meta=r.i32()
        if sfver>=19: r.u64()
        raw.append((nd,toff,noff))
    sb=r.raw(strbuf_size)
    def s(off):
        if off & 0x80000000:
            return COMMON_STRING.get(off & 0x7fffffff, "??%d"%(off&0x7fffffff))
        e=sb.index(b"\0",off); return sb[off:e].decode("utf8","replace")
    for nd,t,nm in raw:
        nd.type=s(t); nd.name=s(nm)
    # build tree
    nodes=[nd for nd,_,_ in raw]
    root=nodes[0]; stack=[root]
    for nd in nodes[1:]:
        while len(stack)>nd.level: stack.pop()
        stack[-1].children.append(nd)
        stack.append(nd)
    return root, nodes

class BR:
    def __init__(self,d,big=False):
        self.d=d; self.p=0; self.big=big
        self.f = ">" if big else "<"
    def prim(self,fmt,n):
        v=struct.unpack_from(self.f+fmt,self.d,self.p)[0]; self.p+=n; return v
    def i32(self): return self.prim("i",4)
    def raw(self,n):
        v=self.d[self.p:self.p+n]; self.p+=n; return v
    def align(self):
        self.p=(self.p+3)//4*4

class BW:
    def __init__(self,big=False):
        self.b=bytearray(); self.f=">" if big else "<"
    def prim(self,fmt,v): self.b+=struct.pack(self.f+fmt,v)
    def i32(self,v): self.prim("i",v)
    def raw(self,d): self.b+=d
    def align(self):
        while len(self.b)%4: self.b.append(0)

def read_value(node, r):
    t=node.type
    align=(node.meta & 0x4000)!=0
    if t in PRIM:
        fmt,n=PRIM[t]; v=r.prim(fmt,n)
    elif t=="string":
        n=r.i32(); v=r.raw(n).decode("utf8","surrogateescape")
        if node.children and (node.children[0].meta & 0x4000): align=True
    elif t=="TypelessData":
        n=r.i32(); v=r.raw(n)
    elif node.children and node.children[0].type=="Array":
        arr=node.children[0]
        if arr.meta & 0x4000: align=True
        n=r.i32()
        elem=arr.children[1]
        v=[read_value(elem,r) for _ in range(n)]
    else:
        v={}
        for c in node.children:
            v[c.name]=read_value(c,r)
    if align: r.align()
    return v

def write_value(node, v, w):
    t=node.type
    align=(node.meta & 0x4000)!=0
    if t in PRIM:
        fmt,n=PRIM[t]; w.prim(fmt,v)
    elif t=="string":
        b=v.encode("utf8","surrogateescape") if isinstance(v,str) else v
        w.i32(len(b)); w.raw(b)
        if node.children and (node.children[0].meta & 0x4000): align=True
    elif t=="TypelessData":
        w.i32(len(v)); w.raw(v)
    elif node.children and node.children[0].type=="Array":
        arr=node.children[0]
        if arr.meta & 0x4000: align=True
        w.i32(len(v))
        elem=arr.children[1]
        for x in v: write_value(elem,x,w)
    else:
        for c in node.children:
            write_value(c, v[c.name], w)
    if align: w.align()
