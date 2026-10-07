import orpaths
import unityser as u, tt, glob, os, json
import orpaths
BASE=orpaths.base_dir()
TARGETS={
 'tooltips':['Name','NamePlural','Description','Action','Type','DiscoveryHint'],
 'dialogue':['Message','Response','DialogueSequences.Text','DialogueSequences.ActionA.Text','DialogueSequences.ActionB.Text','DialogueSequences.ActionC.Text'],
 'tutorialsegment':['Message.Body'],
}
def collect(node, v, path, out):
    if node.type=="string":
        out.append((path, v)); return
    if isinstance(v,dict):
        for c in node.children: collect(c, v[c.name], (path+'.' if path else '')+c.name, out)
    elif isinstance(v,list) and node.children and node.children[0].type=="Array":
        elem=node.children[0].children[1]
        for i,x in enumerate(v): collect(elem, x, path+'[%d]'%i, out)

def run():
    entries=[]
    for key,fields in TARGETS.items():
        f=BASE+'/defaultlocalgroup_assets_%s.bundle'%key
        fs=u.read_bundle(f)
        sf=u.SerializedFile(fs[0][1])
        for o in sf.objects:
            ty=sf.types[o['type_id']]
            if o['class_id']!=114 or 'root' not in ty: continue
            v=tt.read_value(ty['root'], tt.BR(sf.obj_data(o), sf.big))
            out=[]; collect(ty['root'], v, '', out)
            assetname=v.get('m_Name','')
            for p,s in out:
                if not s: continue
                base=p.split('[')[0]
                norm='.'.join(x.split('[')[0] for x in p.split('.'))
                if norm in fields or base in fields:
                    entries.append({'bundle':key,'asset':assetname,'path':p,'en':s})
    json.dump(entries, open(orpaths.out('strings_en.json'),'w'), ensure_ascii=False, indent=0)
    uniq=sorted({e['en'] for e in entries})
    open(orpaths.out('strings_unique.txt'),'w').write('\n'.join(uniq))
    print('entries',len(entries),'unique',len(uniq))
    from collections import Counter
    print(Counter((e['bundle'],e['path'].split('[')[0]) for e in entries).most_common(15))
run()
