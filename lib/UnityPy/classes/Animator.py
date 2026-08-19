from .Behaviour import Behaviour
from .PPtr import PPtr


class Animator(Behaviour):
    def __init__(self, reader):
        super().__init__(reader=reader)

        self.m_Avatar = PPtr(reader)  
        self.m_Controller = PPtr(reader)  
        self.m_CullingMode = reader.read_int()
        version = self.version

        if version >= (4, 5):  
            self.m_UpdateMode = reader.read_int()

        self.m_ApplyRootMotion = reader.read_boolean()
        if (4, 5) < version[2:] <= (5, 0):  
            reader.align_stream()

        if version >= (5,):  
            self.m_LinearVelocityBlending = reader.read_boolean()
            reader.align_stream()

        if version[2:] < (4, 5):  
            self.m_AnimatePhysics = reader.read_boolean()

        if version >= (4, 3):  
            self.m_HasTransformHierarchy = reader.read_boolean()

        if version >= (4, 5):  
            self.m_AllowConstantClipSamplingOptimization = reader.read_boolean()

        if (4,) < version[:1] < (2018,):  
            reader.align_stream()

        if version >= (2018,):  
            self.m_KeepAnimatorControllerStateOnDisable = reader.read_boolean()
            reader.align_stream()
