import orpaths
import numpy as np
from PIL import ImageFont

FONT=orpaths.FONT_TTF
PPEM=11
BEARING_SHIFT=1   # 글리프를 1px 아래로 내려 라틴 베이스라인에 맞춤

def charset():
    cs=[]
    cs+= [chr(c) for c in range(0xAC00,0xD7A4)]          # Hangul syllables
    cs+= [chr(c) for c in range(0x3131,0x318F)]          # compatibility jamo
    cs+= list('·…‘’“”—–―～·「」『』〈〉《》【】')
    cs+= [chr(c) for c in range(0x2460,0x2474)]          # circled numbers
    return list(dict.fromkeys(cs))

def render_all():
    f=ImageFont.truetype(FONT,PPEM)
    asc,desc=f.getmetrics()
    out=[]
    for ch in charset():
        try: m=f.getmask(ch, mode='1')
        except Exception: continue
        w,h=m.size
        if w==0 or h==0:
            out.append((ch,None,0,0,0,0,f.getlength(ch))); continue
        a=np.frombuffer(bytes(m),dtype=np.uint8).reshape(h,w)
        if a.max()==0:
            out.append((ch,None,0,0,0,0,f.getlength(ch))); continue
        bb=f.getbbox(ch)              # (x0,y0,x1,y1) relative to (0, ascender-top)
        ys,xs=np.nonzero(a)
        y0,y1=ys.min(),ys.max(); x0,x1=xs.min(),xs.max()
        crop=a[y0:y1+1, x0:x1+1]
        bearingX = bb[0]+x0
        bearingY = asc - (bb[1]+y0) - BEARING_SHIFT
        out.append((ch,crop,crop.shape[1],crop.shape[0],bearingX,bearingY,round(f.getlength(ch))))
    return out, asc, desc

if __name__=='__main__':
    g,asc,desc=render_all()
    ws=[x[2] for x in g if x[1] is not None]; hs=[x[3] for x in g if x[1] is not None]
    print('glyphs',len(g),'with ink',len(ws))
    print('max w',max(ws),'max h',max(hs),'asc',asc,'desc',desc)
    import collections
    print('adv',collections.Counter(x[6] for x in g).most_common(5))
    print('bearingY',collections.Counter(x[5] for x in g).most_common(5))
    for ch,c,w,h,bx,by,adv in g[:2]+g[11170:11175]:
        print(repr(ch),w,h,bx,by,adv)
