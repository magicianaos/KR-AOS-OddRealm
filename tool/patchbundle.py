import orpaths
import unityser as u, pack, tt

def load(path):
    fs=u.read_bundle(path)
    assert len(fs)==1, fs
    nm,raw=fs[0]
    return nm, u.SerializedFile(raw)

def rebuild(path, mutate):
    """mutate(sf, obj, value_or_None) -> value ; returns new bundle bytes"""
    nm, sf = load(path)
    datas=[]
    for o in sf.objects:
        ty=sf.types[o['type_id']]; d=sf.obj_data(o)
        if 'root' not in ty or o['class_id']!=114:
            datas.append(d); continue
        r=tt.BR(d,sf.big); v=tt.read_value(ty['root'],r)
        assert r.p==len(d)
        changed=mutate(sf,o,v)
        if not changed: datas.append(d); continue
        w=tt.BW(sf.big); tt.write_value(ty['root'],v,w); datas.append(bytes(w.b))
    n=pack.write_serialized(sf,datas)
    return pack.write_bundle([(nm,n)])
