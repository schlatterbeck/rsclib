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
# Vorname

from csv               import DictWriter
from rsclib.HTML_Parse import tag, Page_Tree

class Vorname (Page_Tree) :
    site  = 'http://www.vorname.com'
    url   = 'index.php?keyword=%(name)s&cms=suche'
    delay = 0

    def __init__ (self, name) :
        self.name = name
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
                    and a.text.strip () == self.name
                    ) :
                    count += 1
            self.nmatches = count
    # end def parse

# end class Vorname

if __name__ == "__main__" :
    import sys
    n = "Maximilian"
    if len (sys.argv) > 1 :
        n = sys.argv [1]
    v = Vorname (n)
    print v.nmatches
