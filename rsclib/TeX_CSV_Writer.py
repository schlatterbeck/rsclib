#!/usr/bin/python
# Copyright (C) 2007 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from rsclib.autosuper import autosuper

class TeX_CSV_Writer (autosuper) :
    """ Implement csv functionality for TeX readers -- quote TeX-specific
        characters, use '{' and '}' for quoting fields containing special
        characters.

        >>> from StringIO import StringIO
        >>> io = StringIO ()
        >>> x = TeX_CSV_Writer (io)
        >>> x.writerow (['1&%$#[]{}\\\\','2\\n3'])
        >>> io.getvalue ()
        '1\\\\&\\\\%\\\\$\\\\#\\\\[\\\\]\\\\{\\\\}\\\\backslash;2\\\\\\\\3\\n'
        >>> io = StringIO ()
        >>> x = TeX_CSV_Writer (io)
        >>> x.writerow (['3','4'])
        >>> x.writerow (['3;4','4;5'])
        >>> x.writerow (['5','6\\n7'])
        >>> io.getvalue ()
        '3;4\\n{3;4};{4;5}\\n5;6\\\\\\\\7\\n'
        >>> io = StringIO ()
        >>> x = TeX_CSV_Writer (io)
        >>> x.writerow (['1-2', '1--2', '1 -- 2', '1 - 2', 'a - b', 'a-b'])
        >>> io.getvalue ()
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
