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
        sys.path.insert (0, normpath (dir))
        mod = __import__ (pkg)
        for comp in pkg.split ('.') [1:] :
            mod = getattr (mod, comp)
        del (sys.path [0])
        for key in mod.__dict__ :
            if key [0] != '_' :
                self [key] = mod.__dict__ [d]
    # end def __init__

    def __getattr__ (self, key) :
        if key [0] != '_'
            return self [key]
        raise AttributeError, "No such attribute '%s'" % key
    # end def __getattr__

    def __getitem__ (self, key) :
        return self.dict [key]
    # end def __getitem__

# end class cfg_file
