#!/usr/bin/python
# Copyright (C) 2008 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# ****************************************************************************
#
# Firstname

import os
import pickle
from   rsclib.HTML_Parse import tag, Page_Tree
from   rsclib.autosuper  import autosuper

class _Nonzero (autosuper) :
    def __nonzero__ (self) :
        return bool (self.nmatches)
    # end def __nonzero__
# end class _Nonzero

class Firstname (_Nonzero, Page_Tree) :
    site  = 'http://www.vorname.com'
    url   = 'index.php?keyword=%(name)s&cms=suche'
    delay = 0

    cachename = os.path.join (os.environ.get ('HOME', '/tmp'), '.fn_cache')

    try :
        cache = pickle.load (open (cachename, 'rb'))
    except (IOError, EOFError) :
        cache = {}
        pass

    hardcoded = dict.fromkeys (('Gertraude', 'Gabor'))

    def __init__ (self, name) :
        self.name    = name
        self.uniname = name.decode (self.html_charset)
        if name in self.hardcoded :
            self.nmatches = 1
        elif name in self.cache :
            self.nmatches = self.cache [name]
        else :
            self.__super.__init__ (url = self.url % locals ())
    # end def __init__

    def parse (self) :
        for d in self.tree.getroot ().findall (".//%s" % tag ("div")) :
            if d.get ("class") == "box_content" :
                self.content = d
                break
        else :
            raise ValueError, "No box_content found"
        for t in self.content.findall (".//%s" % tag ("span")) :
            if t.get ("class") == "titel_blue_bold" :
                text = t.text.strip ()
                if text == "leider keine Treffer" :
                    self.nmatches = 0
                else :
                    l = text.split ()
                    assert (l [1] == "Treffer")
                    self.nmatches = int (l [0])
                break
        else :
            raise ValueError, "No matches found"
        if self.nmatches :
            tbl = self.content.find (".//%s" % tag ("table"))
            count = 0
            for a in tbl.findall (".//%s" % tag ("a")) :
                if  (   a.get ("class") == "tabellist"
                    and a.text.strip () == self.uniname
                    ) :
                    count += 1
            self.nmatches = count
        self.cache [self.name] = self.nmatches
    # end def parse

    @classmethod
    def make_cache_persistent (cls) :
        f = open (cls.cachename, 'wb')
        pickle.dump (cls.cache, f)
        f.close ()
    # end def make_cache_persistent

# end class Firstname

class Combined_Firstname (_Nonzero) :
    def __init__ (self, name) :
        self.name = name
        names     = name.split ('-')
        fn        = {}
        for n in names :
            fn [n] = Firstname (n)
        self.nmatches = max (f.nmatches for f in fn.itervalues ())
    # end def __init__
# end class Combined_Firstname

if __name__ == "__main__" :
    import sys
    Firstname.cachename = '/tmp/Firstname_TEST'
    Firstname.cache     = {}
    try :
        os.unlink (Firstname.cachename)
    except (OSError) :
        pass
    for name in sys.argv [1:] :
        v = Combined_Firstname (name)
        if v :
            print "%s: %s" % (name, v.nmatches)
    Firstname.make_cache_persistent ()
