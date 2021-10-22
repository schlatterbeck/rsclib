#!/usr/bin/python3
# Copyright (C) 2005-21 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
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
