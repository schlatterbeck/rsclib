#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
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
#
# Python compatibility. Some code taken from Armin Ronacher's excellent
# blog article on python2 vs. python3 porting, see
#

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from rsclib.autosuper import autosuper

import sys
PY2 = sys.version_info [0] == 2
if PY2 :
    text_type    = unicode
    string_types = (str, unicode)
    unichr       = unichr
else :
    text_type    = str
    string_types = (str,)
    unichr       = chr

if PY2 :
    class ustr (unicode, autosuper) :
        def __repr__ (self) :
            return self.__super.__repr__ ().lstrip ('u')
        # end def __repr__
    # end class ustr
else :
    ustr = text_type
