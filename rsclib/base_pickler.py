#!/usr/bin/python
# Copyright (C) 2013 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from   rsclib.autosuper                import autosuper

class Base_Pickler (autosuper) :
    """ Generic __getstate__ method to allow defining pickle exceptions
    """

    pickle_exceptions = {}

    def __getstate__ (self) :
        d   = dict ()
        for n, k in enumerate (self.__dict__) :
            v = self.__dict__ [k]
            d [k] = self.pickle_exceptions.get (k, v)
        return d
    # end def __getstate__

# end class Base_Pickler
