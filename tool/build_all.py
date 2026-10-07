import orpaths
import sys, glob, json, os
import unityser as u, tt, pack, tx

OUT=orpaths.out('patch')
os.makedirs(OUT, exist_ok=True)

LOOK={}
for d in ('desc','dlg','tut'):
    for f in sorted(glob.glob(os.path.join(orpaths.TOOL,'tr',d,'*.json'))):
        LOOK.update(json.load(open(f)))

stats={}
def T(s, key):
    if not s: return s
    if s in LOOK: r=LOOK[s]
    else: r=tx.translate(s)
    if r!=s: stats[key]=stats.get(key,0)+1
    return r

FIELDS={
 'tooltips': {'Name','NamePlural','Action','Type','Description','DiscoveryHint'},
 'dialogue': {'Message','Response','Text'},
 'tutorialsegment': {'Body','Speaker'},
}
def apply(node, v, key, fields):
    if isinstance(v,dict):
        for c in node.children:
            if c.type=='string':
                if c.name in fields: v[c.name]=T(v[c.name], key+'.'+c.name)
            else:
                apply(c, v[c.name], key, fields)
    elif isinstance(v,list) and node.children and node.children[0].type=='Array':
        elem=node.children[0].children[1]
        if elem.type=='string':
            if node.name in fields:
                for i,x in enumerate(v): v[i]=T(x, key+'.'+node.name)
        else:
            for x in v: apply(elem, x, key, fields)

def run(name):
    src=orpaths.src(name)
    fs=u.read_bundle(src); nm,raw=fs[0]
    sf=u.SerializedFile(raw)
    fields=FIELDS[name]
    datas=[]
    for o in sf.objects:
        ty=sf.types[o['type_id']]; d=sf.obj_data(o)
        if o['class_id']!=114 or 'root' not in ty: datas.append(d); continue
        r=tt.BR(d,sf.big); v=tt.read_value(ty['root'],r); assert r.p==len(d)
        apply(ty['root'], v, name, fields)
        w=tt.BW(sf.big); tt.write_value(ty['root'],v,w); datas.append(bytes(w.b))
    out=pack.write_bundle([(nm, pack.write_serialized(sf,datas))])
    p='%s/defaultlocalgroup_assets_%s.bundle'%(OUT,name)
    open(p,'wb').write(out)
    # verify
    f2=u.read_bundle(p); s2=u.SerializedFile(f2[0][1])
    assert len(s2.objects)==len(sf.objects)
    for o in s2.objects:
        ty=s2.types[o['type_id']]
        if o['class_id']!=114 or 'root' not in ty: continue
        rr=tt.BR(s2.obj_data(o),s2.big); tt.read_value(ty['root'],rr)
        assert rr.p==o['size']
    print('%-18s %8d bytes  (orig %d)'%(name, len(out), os.path.getsize(src)))

for n in FIELDS: run(n)
print(json.dumps(stats, indent=1, ensure_ascii=False))
