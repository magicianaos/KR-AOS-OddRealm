import orpaths
import unityser as u, tt, glob, os, re
from collections import defaultdict

import orpaths
BASE=orpaths.base_dir()
ID_RE=re.compile(r'^[a-z0-9_]+$')
def walk(node, v, path, out):
    t=node.type
    if t=="string":
        out.append((path+"."+node.name, v))
    elif isinstance(v,dict):
        for c in node.children: walk(c, v[c.name], path+"."+node.name, out)
    elif isinstance(v,list) and node.children and node.children[0].type=="Array":
        elem=node.children[0].children[1]
        for x in v: walk(elem, x, path+"."+node.name+"[]", out)

fields=defaultdict(set)
for f in sorted(glob.glob(BASE+'/defaultlocalgroup_assets_*.bundle')):
    try: fs=u.read_bundle(f)
    except Exception: continue
    for nm,data in fs:
        try: sf=u.SerializedFile(data)
        except Exception: continue
        if not sf.enable_typetree: continue
        for o in sf.objects:
            ty=sf.types[o['type_id']]
            if 'root' not in ty: continue
            try: v=tt.read_value(ty['root'], tt.BR(sf.obj_data(o), sf.big))
            except Exception: continue
            out=[]; walk(ty['root'], v, os.path.basename(f)[24:-7], out)
            for p,s in out:
                if s: fields[p].add(s)
def humanish(s):
    if ID_RE.match(s): return False
    if s.startswith('Assets/') or s.startswith('<sprite') or s.startswith('sp_'): return False
    if not re.search(r'[A-Za-z]', s): return False
    return True
for p in sorted(fields):
    vs=fields[p]
    h=[s for s in vs if humanish(s)]
    if not h: continue
    print(f'{p:60s} uniq={len(vs):5d} human={len(h):5d}  e.g. {h[:2]}'[:190])
