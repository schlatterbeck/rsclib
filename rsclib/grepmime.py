#!/usr/bin/python
# Copyright (C) 2007-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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
