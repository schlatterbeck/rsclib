#!/usr/bin/python3
# Copyright (C) 2005-21 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ****************************************************************************

import sys
from rsclib.autosuper import autosuper

class Config_File (autosuper) :
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
        try :
            mod = __import__ (pkg)
            for comp in pkg.split ('.') [1:] :
                mod = getattr (mod, comp)
            for key in mod.__dict__ :
                if key [0] != '_' :
                    self [key] = mod.__dict__ [key]
        except ImportError :
            pass
        del (sys.path [0])
    # end def __init__

    def __getattr__ (self, key) :
        try :
            if key [0] != '_' :
                return self [key]
        except KeyError :
            raise AttributeError \
                ( "%s instance has no attribute '%s'"
                % (self.__class__.__name__, key)
                )
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
    __contains__ = has_key

    def get (self, key, val = None) :
        return self.dict.get (key, val)
    # end def get

# end class Config_File
