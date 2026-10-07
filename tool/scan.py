import unityser as u, tt, glob, os, json, re
from collections import Counter, defaultdict

import orpaths
BASE=orpaths.base_dir()

def walk(node, v, path, out):
    t=node.type
    if t=="string":
        out.append((path+"."+node.name if node.name else path, v))
    elif isinstance(v,dict):
        for c in node.children:
            walk(c, v[c.name], path+"."+node.name, out)
    elif isinstance(v,list) and node.children and node.children[0].type=="Array":
        elem=node.children[0].children[1]
        for x in v: walk(elem, x, path+"."+node.name+"[]", out)

fieldc=Counter(); vals=defaultdict(set)
files=sorted(glob.glob(BASE+'/defaultlocalgroup_assets_*.bundle'))
for f in files:
    try: fs=u.read_bundle(f)
    except Exception as e: print('ERR',f,e); continue
    for nm,data in fs:
        try: sf=u.SerializedFile(data)
        except Exception as e: continue
        if not sf.enable_typetree: continue
        for o in sf.objects:
            ty=sf.types[o['type_id']]
            if 'root' not in ty: continue
            d=sf.obj_data(o)
            try:
                r=tt.BR(d, sf.big); v=tt.read_value(ty['root'], r)
            except Exception as e: continue
            out=[]
            walk(ty['root'], v, os.path.basename(f)[24:-7], out)
            for p,s in out:
                if not s: continue
                fieldc[p]+=1
                vals[p].add(s)
print(len(files),'bundles')
for p,c in fieldc.most_common(60):
    sample=list(vals[p])[:2]
    print(f'{c:6d} {len(vals[p]):6d}  {p}   {sample}'[:200])
