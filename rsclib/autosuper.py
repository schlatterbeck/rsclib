#!/usr/bin/python
# Note: This is from Guido van Rossums "Unifying types and classes in
# Python 2.2" metaclass example.
# http://www.python.org/download/releases/2.2/descrintro/

from rsclib.pycompat import with_metaclass

class _autosuper (type) :
    def __init__ (cls, name, bases, dict) :
        super   (_autosuper, cls).__init__ (name, bases, dict)
        setattr (cls, "_%s__super" % name, super (cls))
    # end def __init__
# end class _autosuper

class autosuper (with_metaclass (_autosuper)) :
    """ Test new autsuper magic
    >>> from autosuper import autosuper
    >>> class X (autosuper, dict) :
    ...     def __init__ (self, *args, **kw) :
    ...         return self.__super.__init__ (*args, **kw)
    ...
    >>> X((x,1) for x in range(3))
    {0: 1, 1: 1, 2: 1}
    >>> class Y (autosuper) :
    ...     def __repr__ (self) :
    ...         return "class Y"
    ...
    >>> Y((x,1) for x in range(23))
    class Y
    """

    def __init__ (self, *args, **kw) :
        try :
            oc =  self.__super.__init__.__objclass__
        except AttributeError :
            oc = None
        if oc is object :
            self.__super.__init__ ()
        else :
            self.__super.__init__ (*args, **kw)
    # end def __init__
# end class autosuper
