import struct
import math

MaxValue = 65504.0
MinValue = -65504.0


def ToHalf(*args) -> float:
    """
    Converts the input into a half-float.
    Inputs:
        unsigned integer
        or
        buffer (bytes, buffer)
        offset
    """
    
    if len(args) == 1:
        data = struct.pack("H", args[0])
        val = struct.unpack("e", data)[0]
    
    elif len(args) == 2:
        val = struct.unpack_from("e", args[0], args[1])[0]
    else:
        raise ValueError("Invalid amount of arguments")

    if math.isnan(val):
        
        return 0
    elif math.isinf(val):
        return MaxValue

    return val





































































