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

from __future__ import unicode_literals
from rsclib.pycompat import ustr
import re
from rsclib.autosuper import autosuper
try :
    from io import StringIO
except ImportError :
    from StringIO import StringIO

class TeX_CSV_Writer (autosuper) :
    """ Implement csv functionality for TeX readers -- quote TeX-specific
        characters, use '{' and '}' for quoting fields containing special
        characters.

        >>> io = StringIO ()
        >>> x = TeX_CSV_Writer (io)
        >>> x.writerow (['1&%$#[]{}\\\\','2\\n3'])
        >>> ustr (io.getvalue ())
        '1\\\\&\\\\%\\\\$\\\\#\\\\[\\\\]\\\\{\\\\}\\\\backslash;2\\\\\\\\3\\n'
        >>> io = StringIO ()
        >>> x = TeX_CSV_Writer (io)
        >>> x.writerow (['3','4'])
        >>> x.writerow (['3;4','4;5'])
        >>> x.writerow (['5','6\\n7'])
        >>> ustr (io.getvalue ())
        '3;4\\n{3;4};{4;5}\\n5;6\\\\\\\\7\\n'
        >>> io = StringIO ()
        >>> x = TeX_CSV_Writer (io)
        >>> x.writerow (['1-2', '1--2', '1 -- 2', '1 - 2', 'a - b', 'a-b'])
        >>> ustr (io.getvalue ())
        '1--2;1--2;1--2;1--2;a -- b;a-b\\n'
    """

    quote      = \
        { 'german'  : ('"`',  '"\'')
        , 'english' : ('\\`', '\\\'')
        }
    need_quote = dict.fromkeys ('#{}[]$&%')
    replace    = \
        { '\\' : '\\backslash'
        , '\n' : '\\\\'
        }
    numpattern = re.compile (r'(\d)[ ]*--?[ ]*(\d)')

    def __init__ \
        ( self
        , file
        , delimiter      = ';'
        , quotechar      = '\\'
        , lineterminator = '\n'
        , language       = 'german'
        , **kw
        ) :
        self.file           = file
        self.quotechar      = quotechar
        self.delimiter      = delimiter
        self.lineterminator = lineterminator
        self.language       = language
    # end def __init__

    def writerow (self, columns) :
        newcols = []
        for col in columns :
            quote_idx = False
            delimit   = False
            newcol    = []
            for c in col :
                if c == self.delimiter :
                    delimit = True
                if c == '"' :
                    newcol.append (self.quote [self.language][quote_idx])
                    quote_idx = not quote_idx
                elif c == '/' :
                    newcol.append ('\\discretionary{/}{}{/}')
                elif c in self.need_quote :
                    newcol.append (self.quotechar + c)
                elif c in self.replace :
                    newcol.append (self.replace [c])
                else :
                    newcol.append (c)
            result = ''.join (newcol)
            # fix broken dashes:
            result = result.replace (' - ', ' -- ')
            result = self.numpattern.sub (r'\1--\2', result)
            if delimit :
                result = '{' + result + '}'
            newcols.append (result)
        self.file.write (self.delimiter.join (newcols))
        self.file.write (self.lineterminator)
    # end def writerow
# end class TeX_CSV_Writer

class TeX_CSV_Dict_Writer (TeX_CSV_Writer) :
    def __init__ (self, file, fields, ** kw) :
        self.__super.__init__ (file, ** kw)
        self.fields = fields
    # end def __init__

    def writerow (self, rowdict) :
        self.__super.writerow (rowdict [k] for k in self.fields)
    # end def writerow
# end class TeX_CSV_Writer
