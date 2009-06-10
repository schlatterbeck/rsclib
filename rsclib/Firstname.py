#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008 Dr. Ralf Schlatterbeck Open Source Consulting.
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

    hardcoded = \
        { 'Dorett'      : (False, True)
        , 'Doritt'      : (False, True)
        , 'Dorrit'      : (False, True)
        , 'Eleonore'    : (False, True)
        , 'Gabor'       : (True,  False)
        , 'Gertraude'   : (False, True)
        , 'Gliceria'    : (False, True)
        , 'Hanns'       : (True,  False)
        , 'Heinzwerner' : (True,  False)
        , 'Henryk'      : (True,  False)
        , 'Hildgard'    : (False, True)
        , 'Ingulf'      : (True,  False)
        , 'Irmentraut'  : (False, True)
        , 'Karlos'      : (True,  False)
        , 'Karlotte'    : (False, True)
        , 'Krystyna'    : (False, True)
        , 'Libuse'      : (False, True)
        , 'Margerita'   : (False, True)
        , 'Rudolfine'   : (False, True)
        , 'Siegrid'     : (False, True)
        , 'Silvie'      : (False, True)
        , 'Suse'        : (False, True)
        , 'Traude'      : (False, True)
        , 'Trude'       : (False, True)
        , 'Waltraude'   : (False, True)
        #                  male   female
        }

    def __init__ (self, name, strip_punctiation = True) :
        if strip_punctiation :
            name = name.strip ('.,; \t\r\n')
        self.name      = name
        self.is_male   = False
        self.is_female = False
        self.uniname   = name.decode (self.html_charset)
        self.nmatches  = 0
        if name in self.hardcoded :
            self.nmatches = 1
            self.is_male, self.is_female = self.hardcoded [name]
        elif len (name) < 2 :
            pass
        elif name in self.cache :
            self.nmatches, self.is_male, self.is_female = self.cache [name]
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
            for tr in tbl :
                for a in tr.findall (".//%s" % tag ("a")) :
                    if  (   a.get ("class") == "tabellist"
                        and a.text.strip () == self.uniname
                        ) :
                        count += 1
                        sex = self.get_text (tr [1]).strip ()
                        m, w = \
                            (x.decode ('latin1')
                             for x in ('männlich', 'weiblich')
                            )
                        if sex == m : self.is_male   = True
                        if sex == w : self.is_female = True
            self.nmatches = count
        self.cache [self.name] = (self.nmatches, self.is_male, self.is_female)
    # end def parse

    @classmethod
    def make_cache_persistent (cls) :
        f = open (cls.cachename, 'wb')
        pickle.dump (cls.cache, f)
        f.close ()
    # end def make_cache_persistent
# end class Firstname

class Combined_Firstname (_Nonzero) :
    def __init__ (self, name, strip_punctiation = True) :
        self.name = name
        names     = name.split ('-')
        fn        = {}
        for n in names :
            fn [n] = Firstname (n, strip_punctiation = strip_punctiation)
        self.nmatches  = min  (f.nmatches for f in fn.itervalues ())
        self.is_male   = bool (min (f.is_male   for f in fn.itervalues ()))
        self.is_female = bool (min (f.is_female for f in fn.itervalues ()))
    # end def __init__

    @staticmethod
    def make_cache_persistent () :
        Firstname.make_cache_persistent ()
    # end def make_cache_persistent
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
            print "%s: %s male: %s female: %s" \
                % (name, v.nmatches, v.is_male, v.is_female)
    Firstname.make_cache_persistent ()
