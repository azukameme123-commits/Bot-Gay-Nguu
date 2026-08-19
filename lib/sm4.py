import Protect as p

class SM4Key:

    def __init__(self, k):
        self.k = bytes(k)

    def decrypt(self, d, initial=None):
        return p.sm4_cbc_decrypt_partial(bytes(d), self.k, bytes(initial) if initial is not None else bytes(16))

    def encrypt(self, d, initial=None):
        return p.sm4_cbc_encrypt_partial(bytes(d), self.k, bytes(initial) if initial is not None else bytes(16))
