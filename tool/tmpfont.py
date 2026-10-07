import tt
A=0x4000
def N(type,name,align=False,children=None,size=-1):
    n=tt.Node(); n.type=type; n.name=name; n.meta=A if align else 0
    n.children=children or []; n.size=size; n.version=1; n.level=0; n.flags=0; n.index=0
    return n
def STR(name): return N("string",name,False,[N("Array","Array",True,[N("int","size"),N("char","data")])])
def PPTR(t,name): return N("PPtr<%s>"%t,name,False,[N("int","m_FileID"),N("SInt64","m_PathID")])
def VEC(name,elem): return N("vector",name,False,[N("Array","Array",True,[N("int","size"),elem])])
def F(name): return N("float",name)
def I(name): return N("int",name)
def U(name): return N("unsigned int",name)
def B(name): return N("bool",name,True)

GlyphMetrics=N("GlyphMetrics","m_Metrics",False,[F("m_Width"),F("m_Height"),F("m_HorizontalBearingX"),F("m_HorizontalBearingY"),F("m_HorizontalAdvance")])
GlyphRect=lambda nm: N("GlyphRect",nm,False,[I("m_X"),I("m_Y"),I("m_Width"),I("m_Height")])
Glyph=N("Glyph","data",False,[U("m_Index"),GlyphMetrics,GlyphRect("m_GlyphRect"),F("m_Scale"),I("m_AtlasIndex"),I("m_ClassDefinitionType")])
Character=N("TMP_Character","data",False,[N("UInt8","m_ElementType",True),U("m_Unicode"),U("m_GlyphIndex"),F("m_Scale")])
FaceInfo=N("FaceInfo","m_FaceInfo",False,[I("m_FaceIndex"),STR("m_FamilyName"),STR("m_StyleName"),
    F("m_PointSize"),F("m_Scale"),I("m_UnitsPerEM"),F("m_LineHeight"),F("m_AscentLine"),F("m_CapLine"),
    F("m_MeanLine"),F("m_Baseline"),F("m_DescentLine"),F("m_SuperscriptOffset"),F("m_SuperscriptSize"),
    F("m_SubscriptOffset"),F("m_SubscriptSize"),F("m_UnderlineOffset"),F("m_UnderlineThickness"),
    F("m_StrikethroughOffset"),F("m_StrikethroughThickness"),F("m_TabWidth")])
Creation=N("FontAssetCreationSettings","m_CreationSettings",False,[STR("sourceFontFileName"),STR("sourceFontFileGUID"),
    I("faceIndex"),I("pointSizeSamplingMode"),I("pointSize"),I("padding"),I("paddingMode"),I("packingMode"),
    I("atlasWidth"),I("atlasHeight"),I("characterSetSelectionMode"),STR("characterSequence"),
    STR("referencedFontAssetGUID"),STR("referencedTextAssetGUID"),I("fontStyle"),F("fontStyleModifier"),
    I("renderMode"),B("includeFontFeatures")])
FeatureTable=N("TMP_FontFeatureTable","m_FontFeatureTable",False,[
    VEC("m_MultipleSubstitutionRecords",N("MultipleSubstitutionRecord","data",False,[U("x")])),
    VEC("m_LigatureSubstitutionRecords",N("LigatureSubstitutionRecord","data",False,[U("x")])),
    VEC("m_GlyphPairAdjustmentRecords",N("GlyphPairAdjustmentRecord","data",False,[U("x")])),
    VEC("m_MarkToBaseAdjustmentRecords",N("MarkToBaseAdjustmentRecord","data",False,[U("x")])),
    VEC("m_MarkToMarkAdjustmentRecords",N("MarkToMarkAdjustmentRecord","data",False,[U("x")])),
])
WeightPair=N("TMP_FontWeightPair","data",False,[PPTR("MonoBehaviour","regularTypeface"),PPTR("MonoBehaviour","italicTypeface")])
LegacyFace=N("FaceInfo_Legacy","m_fontInfo",False,[STR("Name"),F("PointSize"),F("Scale"),I("CharacterCount"),
    F("LineHeight"),F("Baseline"),F("Ascender"),F("CapHeight"),F("Descender"),F("CenterLine"),
    F("SuperscriptOffset"),F("SubscriptOffset"),F("SubSize"),F("Underline"),F("UnderlineThickness"),
    F("strikethrough"),F("strikethroughThickness"),F("TabWidth"),F("Padding"),F("AtlasWidth"),F("AtlasHeight")])
LegacyGlyph=N("TMP_Glyph","data",False,[I("id"),F("x"),F("y"),F("width"),F("height"),F("xOffset"),F("yOffset"),F("xAdvance"),F("scale")])
KerningTable=N("KerningTable","m_KerningTable",False,[VEC("kerningPairs",N("KerningPair","data",False,[U("x")]))])

ROOT=N("MonoBehaviour","Base",False,[
    PPTR("GameObject","m_GameObject"),
    N("UInt8","m_Enabled",True),
    PPTR("MonoScript","m_Script"),
    STR("m_Name"),
    STR("m_Version"),
    FaceInfo,
    PPTR("Material","m_Material"),
    STR("m_SourceFontFileGUID"),
    Creation,
    PPTR("Font","m_SourceFontFile"),
    STR("m_SourceFontFilePath"),
    I("m_AtlasPopulationMode"),
    B("InternalDynamicOS"),
    VEC("m_GlyphTable",Glyph),
    VEC("m_CharacterTable",Character),
    VEC("m_AtlasTextures",PPTR("Texture2D","data")),
    I("m_AtlasTextureIndex"),
    B("m_IsMultiAtlasTexturesEnabled"),
    B("m_GetFontFeatures"),
    B("m_ClearDynamicDataOnBuild"),
    I("m_AtlasWidth"),I("m_AtlasHeight"),I("m_AtlasPadding"),I("m_AtlasRenderMode"),
    VEC("m_UsedGlyphRects",GlyphRect("data")),
    VEC("m_FreeGlyphRects",GlyphRect("data")),
    FeatureTable,
    B("m_ShouldReimportFontFeatures"),
    VEC("m_FallbackFontAssetTable",PPTR("MonoBehaviour","data")),
    VEC("m_FontWeightTable",WeightPair),
    VEC("fontWeights",WeightPair),
    F("normalStyle"),F("normalSpacingOffset"),F("boldStyle"),F("boldSpacing"),
    N("UInt8","italicStyle",True),N("UInt8","tabSize",True),
    LegacyFace,
    VEC("m_glyphInfoList",LegacyGlyph),
    KerningTable,
    VEC("fallbackFontAssets",PPTR("MonoBehaviour","data")),
    PPTR("Texture2D","atlas"),
])
