from enum import IntEnum




class ExtendableEnum(IntEnum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, int):
            pseudo_member = cls._value2member_map_.get(value, None)
            if pseudo_member is None:
                new_member = int.__new__(cls, value)
                
                
                new_member._name_ = f"Unknown ({value})"
                new_member._value_ = value
                pseudo_member = cls._value2member_map_.setdefault(value, new_member)
            return pseudo_member
        return None  
