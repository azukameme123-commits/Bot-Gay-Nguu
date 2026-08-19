from .Object import Object


class PlayerSettings(Object):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (5, 4):  
            self.productGUID = reader.read_bytes(16)

        self.AndroidProfiler = reader.read_boolean()
        
        
        reader.align_stream()
        self.defaultScreenOrientation = reader.read_int()
        self.targetDevice = reader.read_int()
        if version < (5, 3):  
            if version < (5,):  
                self.targetPlatform = reader.read_int()  
                if version >= (4, 6):  
                    self.targetIOSGraphics = reader.read_int()
            self.targetResolution = reader.read_int()
        else:
            self.useOnDemandResources = reader.read_boolean()
            reader.align_stream()
        if version >= (3, 5):  
            self.accelerometerFrequency = reader.read_int()
        self.companyName = reader.read_aligned_string()
        self.productName = reader.read_aligned_string()
