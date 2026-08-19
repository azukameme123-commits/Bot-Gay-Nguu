
FALLBACK_UNITY_VERSION = "2.5.0f5"



SERIALIZED_FILE_PARSE_TYPETREE = True


FALLBACK_VERSION_WARNED = False  



def get_fallback_version():
    global FALLBACK_VERSION_WARNED
    if not FALLBACK_VERSION_WARNED:
        print(
            f"Warning: 0.0.0 version found, defaulting to UnityPy.config.FALLBACK_UNITY_VERSION ({FALLBACK_UNITY_VERSION})"  
        )
        FALLBACK_VERSION_WARNED = True
    return FALLBACK_UNITY_VERSION
