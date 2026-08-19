from .NamedObject import NamedObject


class MonoScript(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (3, 4):  
            self.m_ExecutionOrder = reader.read_int()
        if version < (5,):  
            self.m_PropertiesHash = reader.read_u_int()
        else:
            self.m_PropertiesHash = reader.read_bytes(16)
        if version < (3,):  
            self.m_PathName = reader.read_aligned_string()

        self.m_ClassName = reader.read_aligned_string()
        if version >= (3,):  
            self.m_Namespace = reader.read_aligned_string()

        self.m_AssemblyName = reader.read_aligned_string()
        if version < (2018, 2):  
            self.m_IsEditorScript = reader.read_boolean()
