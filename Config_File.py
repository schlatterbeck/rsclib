import sys

class cfg_file :
    """
        Configuration information
        We accept a directory for reading configs from, a configuration
        file name (read from this directory in python syntax via pythons
        import mechanism, so it is without .py extension) and key-value
        pairs for config defaults.
    """

    def __init__ (self, dir, pkg, **kw) :
        self.dict = {}
        for key in kw :
            self.dict [key] = kw [key]
        sys.path.insert (0, dir)
        mod = __import__ (pkg)
        for comp in pkg.split ('.') [1:] :
            mod = getattr (mod, comp)
        del (sys.path [0])
        for key in mod.__dict__ :
            if key [0] != '_' :
                self [key] = mod.__dict__ [key]
    # end def __init__

    def __getattr__ (self, key) :
        if key [0] != '_' :
            return self [key]
        raise AttributeError, \
            "%s instance has no attribute '%s'" % (self.__class__.__name__, key)
    # end def __getattr__

    def __getitem__ (self, key) :
        return self.dict [key]
    # end def __getitem__

    def __setitem__ (self, key, val) :
        self.dict [key] = val
    # end def __setitem__

    def has_key (self, key) :
        return self.dict.has_key (key)
    # end def has_key

    def get (self, key, val) :
        return self.dict.get (key, val)
    # end def get

# end class cfg_file
