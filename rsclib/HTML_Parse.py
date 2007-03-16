#!/usr/bin/python2.4

import csv
import re
import sys
from elementtidy      import TidyHTMLTreeBuilder
from urllib           import urlopen
from StringIO         import StringIO
from rsclib.autosuper import autosuper

namespace   = 'http://www.w3.org/1999/xhtml'

def tag (name) :
    return "{%s}%s" % (namespace, name)

class Page_Tree (autosuper) :
    def __init__ \
        (self, site = site, url = url, charset = 'latin1', verbose = 0) :
        self.site    = site
        self.url     = '/'.join ((site, url))
        self.charset = charset
        self.verbose = verbose
        text         = urlopen (self.url).read ().replace ('\0', '')
        self.tree    = TidyHTMLTreeBuilder.parse (StringIO (text))
        self.parse ()
    # end def __init__

    def as_string (self, n = None, indent = 0, with_text = False) :
        s = ["    " * indent]
        if n is None :
            n = self.tree.getroot ()
        s.append (n.tag)
        for attr in sorted (n.attrib.keys ()) :
            s.append (' %s="%s"' % (attr, n.attrib [attr]))
            if with_text :
                if n.text :
                    s.append (" TEXT: %s" % n.text)
                if n.tail :
                    s.append (" TAIL: %s" % n.tail)
        except UnicodeEncodeError :
            pass
        return ''.join (s).encode (self.charset)
    # end def as_string

    def tree_as_string (self, n = None, indent = 0, with_text = False) :
        if n is None :
            n = self.tree.getroot ()
        s = [self.as_string (n, with_text = with_text)]
        for sub in n :
            s.append \
                (self.tree_as_string (sub, indent + 1, with_text = with_text))
        return ''.join (s)
    # end def tree_as_string

    def parse (self) :
        raise NotImplementedError
    # end def parse
# end class Page_Tree
