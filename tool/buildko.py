import orpaths
import unityser as u, tt, tmpfont, tex, tmpset, pack, mkfont
import numpy as np, struct, copy

SRC=orpaths.src('resources')
DST=orpaths.out('resources.assets')
FONT_PID=19174    # 'test'
TEX_PID=340       # 'test Atlas'
SET_PID=19185     # TMP Settings
AW=2048; AH=768

def build_atlas(glyphs):
    img=np.zeros((AH,AW),dtype=np.uint8)   # row 0 = TOP (we flip at the end)
    x=y=0; rowh=0; rects={}
    for ch,crop,w,h,bx,by,adv in glyphs:
        if crop is None: rects[ch]=None; continue
        if x+w>AW: x=0; y+=rowh+1; rowh=0
        if y+h>AH: raise SystemExit('atlas too small')
        img[y:y+h, x:x+w]=np.where(crop>0,255,0)
        rects[ch]=(x,y,w,h)
        x+=w+1; rowh=max(rowh,h)
    used_h=y+rowh
    flipped=img[::-1,:]                     # row 0 = BOTTOM for Unity
    return flipped, rects, used_h

def main():
    glyphs,asc,desc=mkfont.render_all()
    img,rects,used=build_atlas(glyphs)
    print('atlas rows used',used,'of',AH)
    d=open(SRC,'rb').read()
    sf=u.SerializedFile(d)
    byid={o['path_id']:i for i,o in enumerate(sf.objects)}
    datas=[sf.obj_data(o) for o in sf.objects]

    # ---- font asset ----
    fo=sf.objects[byid[FONT_PID]]
    fv=tt.read_value(tmpfont.ROOT, tt.BR(sf.obj_data(fo),False))
    fi=fv['m_FaceInfo']
    fi.update(dict(m_FamilyName='Galmuri11', m_StyleName='Regular', m_FaceIndex=0,
                   m_PointSize=16.0, m_Scale=0.7, m_UnitsPerEM=1000,
                   m_LineHeight=9.0, m_AscentLine=7.0, m_CapLine=7.0, m_MeanLine=5.0,
                   m_Baseline=0.0, m_DescentLine=0.0,
                   m_SuperscriptOffset=7.0, m_SuperscriptSize=0.5,
                   m_SubscriptOffset=-1.0, m_SubscriptSize=0.5,
                   m_UnderlineOffset=-1.0, m_UnderlineThickness=1.0,
                   m_StrikethroughOffset=3.0, m_StrikethroughThickness=1.0,
                   m_TabWidth=3.0))
    gt=[]; ct=[]; idx=0
    for ch,crop,w,h,bx,by,adv in glyphs:
        r=rects.get(ch)
        if r is None: continue
        idx+=1
        gx,gy_top,gw,gh=r
        gy=AH-gy_top-gh          # convert to bottom-origin
        gt.append({'m_Index':idx,
                   'm_Metrics':{'m_Width':float(gw),'m_Height':float(gh),
                                'm_HorizontalBearingX':float(bx),'m_HorizontalBearingY':float(by),
                                'm_HorizontalAdvance':float(adv)},
                   'm_GlyphRect':{'m_X':gx,'m_Y':gy,'m_Width':gw,'m_Height':gh},
                   'm_Scale':1.0,'m_AtlasIndex':0,'m_ClassDefinitionType':0})
        ct.append({'m_ElementType':1,'m_Unicode':ord(ch),'m_GlyphIndex':idx,'m_Scale':1.0})
    fv['m_GlyphTable']=gt; fv['m_CharacterTable']=ct
    fv['m_AtlasTextures']=[{'m_FileID':0,'m_PathID':TEX_PID}]
    fv['m_AtlasTextureIndex']=0
    fv['m_AtlasWidth']=AW; fv['m_AtlasHeight']=AH; fv['m_AtlasPadding']=0
    fv['m_UsedGlyphRects']=[]; fv['m_FreeGlyphRects']=[]
    fv['m_AtlasPopulationMode']=0; fv['InternalDynamicOS']=False
    fv['m_SourceFontFile']={'m_FileID':0,'m_PathID':0}
    fv['m_SourceFontFilePath']=''; fv['m_SourceFontFileGUID']=''
    fv['m_IsMultiAtlasTexturesEnabled']=False
    cs=fv['m_CreationSettings']
    cs.update(dict(sourceFontFileName='Galmuri11', sourceFontFileGUID='', pointSize=16, padding=0,
                   atlasWidth=AW, atlasHeight=AH, characterSequence='Korean', renderMode=fv['m_AtlasRenderMode']))
    fv['m_FallbackFontAssetTable']=[]
    w=tt.BW(False); tt.write_value(tmpfont.ROOT,fv,w)
    datas[byid[FONT_PID]]=bytes(w.b)
    print('font asset bytes',len(w.b),'glyphs',len(gt))

    # ---- atlas texture ----
    to=sf.objects[byid[TEX_PID]]
    tv=tt.read_value(tex.ROOT, tt.BR(sf.obj_data(to),False))
    raw=img.tobytes()
    tv.update({'m_Width':AW,'m_Height':AH,'m_CompleteImageSize':len(raw),'m_MipsStripped':0,
               'm_TextureFormat':1,'m_MipCount':1,'m_IsReadable':0,'m_IsPreProcessed':0,
               'm_IgnoreMipmapLimit':1,'m_StreamingMipmaps':0,'m_StreamingMipmapsPriority':0,
               'm_ImageCount':1,'m_TextureDimension':2,'m_LightmapFormat':0,'m_ColorSpace':0,
               'm_PlatformBlob':[]})
    tv['m_TextureSettings'].update({'m_FilterMode':0,'m_Aniso':1,'m_MipBias':0.0,'m_WrapU':1,'m_WrapV':1,'m_WrapW':1})
    tv['image data']=raw
    tv['m_StreamData']={'offset':0,'size':0,'path':''}
    w2=tt.BW(False); tt.write_value(tex.ROOT,tv,w2)
    datas[byid[TEX_PID]]=bytes(w2.b)
    print('texture bytes',len(w2.b))

    # ---- TMP settings ----
    so=sf.objects[byid[SET_PID]]
    sv=tt.read_value(tmpset.ROOT, tt.BR(sf.obj_data(so),False))
    fb=[x for x in sv['m_fallbackFontAssets'] if x['m_PathID']!=FONT_PID]
    sv['m_fallbackFontAssets']=[{'m_FileID':0,'m_PathID':FONT_PID}]+fb
    sv['m_UseModernHangulLineBreakingRules']=True
    w3=tt.BW(False); tt.write_value(tmpset.ROOT,sv,w3)
    datas[byid[SET_PID]]=bytes(w3.b)
    print('settings fallbacks',sv['m_fallbackFontAssets'])

    out=pack.write_serialized(sf,datas)
    open(DST,'wb').write(out)
    print('resources.assets',len(out),'was',len(d))

    # verify re-read
    sf2=u.SerializedFile(open(DST,'rb').read())
    b2={o['path_id']:o for o in sf2.objects}
    v=tt.read_value(tmpfont.ROOT, tt.BR(sf2.obj_data(b2[FONT_PID]),False))
    print('verify font glyphs',len(v['m_GlyphTable']),'atlas',v['m_AtlasWidth'],v['m_AtlasTextures'])
    v2=tt.read_value(tex.ROOT, tt.BR(sf2.obj_data(b2[TEX_PID]),False))
    print('verify tex',v2['m_Width'],v2['m_Height'],len(v2['image data']),v2['m_StreamData'])

main()
