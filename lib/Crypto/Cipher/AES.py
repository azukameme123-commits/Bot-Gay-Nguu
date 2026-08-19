import Protect as p
MODE_CBC = 2

class C:

    def __init__(self, k, m, v):
        if m != MODE_CBC:
            raise NotImplementedError(m)
        self.k = bytes(k)
        self.v = bytes(v)

    def decrypt(self, d):
        return p.aes_cbc_decrypt(bytes(d), self.k, self.v)

    def encrypt(self, d):
        return p.aes_cbc_encrypt(bytes(d), self.k, self.v)

def new(k, m, v):
    return C(k, m, v)
