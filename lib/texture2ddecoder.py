def __getattr__(n):

    def f(*a, **k):
        raise NotImplementedError(n)
    return f
