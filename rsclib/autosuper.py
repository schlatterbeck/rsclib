#!/usr/bin/python
# Note: This is from Guido van Rossums "Unifying types and classes in
# Python 2.2" metaclass example.
# http://www.python.org/download/releases/2.2/descrintro/

class _autosuper (type) :
    def __init__ (cls, name, bases, dict) :
        super   (_autosuper, cls).__init__ (name, bases, dict)
        setattr (cls, "_%s__super" % name, super (cls))
    # end def __init__
# end class _autosuper

class autosuper (object) :
    __metaclass__ = _autosuper
    def __init__ (self, *args, **kw) :
        if self.__super.__init__.__objclass__ is object :
            self.__super.__init__ ()
        else :
            self.__super.__init__ (*args, **kw)
    # end def __init__
# end class autosuper
