#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2007-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import re
from   email               import message_from_file
from   rsclib.autosuper    import autosuper

class Mail (autosuper) :
    def __init__ (self, fd) :
        self.msg    = message_from_file (fd)
    # end def __init__

    def grep (self, pattern, stop_on_match = False) :
        pattern = re.compile (pattern)
        found = []
        for part in self.msg.walk () :
            if part.get_content_maintype () == 'text' :
                payload = part.get_payload (decode = 1)
                for line in payload.split ('\n') :
                    if pattern.search (line) :
                        found.append (line)
                        if stop_on_match :
                            return found
        return found
    # end def grep

    def __getattr__ (self, name) :
        """
            Delegate everything to our msg
        """
        if not name.startswith ('__') :
            result = getattr (self.msg, name)
            setattr (self, name, result)
            return result
        raise AttributeError (name)
    # end def __getattr__

# end class Mail

if __name__ == "__main__" :
    import sys
    sys.exit (bool (Mail (sys.stdin).grep ('huhu')))
