import tt
from tmpfont import N,STR,PPTR,VEC,F,I,B
def build():
    ch=[STR("m_Name"),
        N("UInt8","m_DownscaleFallback"),N("UInt8","m_IsAlphaChannelOptional",True),
        I("m_Width"),I("m_Height"),I("m_CompleteImageSize"),I("m_MipsStripped"),I("m_TextureFormat"),
        I("m_MipCount"),
        N("UInt8","m_IsReadable"),N("UInt8","m_IsPreProcessed"),N("UInt8","m_IgnoreMipmapLimit"),
        N("UInt8","m_StreamingMipmaps",True),
        I("m_StreamingMipmapsPriority"),
        STR("m_MipmapLimitGroupName"),
        I("m_Unknown0"),
        I("m_ImageCount"),I("m_TextureDimension"),
        N("GLTextureSettings","m_TextureSettings",False,[I("m_FilterMode"),I("m_Aniso"),F("m_MipBias"),I("m_WrapU"),I("m_WrapV"),I("m_WrapW")]),
        I("m_LightmapFormat"),I("m_ColorSpace"),
        N("vector","m_PlatformBlob",False,[N("Array","Array",True,[I("size"),N("UInt8","data")])]),
        N("TypelessData","image data"),
        N("StreamingInfo","m_StreamData",False,[N("SInt64","offset"),N("unsigned int","size"),STR("path")]),
    ]
    return N("Texture2D","Base",False,ch)
ROOT=build()
