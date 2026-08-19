__version__ = "1.9.24"

from .environment import Environment



def load(*args):
    return Environment(*args)



AssetsManager = Environment
