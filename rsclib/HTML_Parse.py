#!/usr/bin/python2.4

from urllib                          import urlopen
from elementtidy.TidyHTMLTreeBuilder import TidyHTMLTreeBuilder
from elementtree.ElementTree         import ElementTree
from rsclib.autosuper                import autosuper

namespace   = 'http://www.w3.org/1999/xhtml'

def tag (name) :
    return "{%s}%s" % (namespace, name)

class Page_Tree (autosuper) :
    def __init__ \
        ( self
        , site         = None
        , url          = None
        , charset      = 'latin1'
        , verbose      = 0
        , html_charset = None
        ) :
        if site :
            self.site = site
        if url :
            self.url  = url
        self.url     = '/'.join ((self.site, self.url))
        self.charset = charset
        self.verbose = verbose
        text         = urlopen (self.url).read ().replace ('\0', '')
        builder      = TidyHTMLTreeBuilder (encoding = html_charset)
        builder.feed (text)
        self.tree    = ElementTree (builder.close ())
        self.parse ()
    # end def __init__

    def as_string (self, n = None, indent = 0, with_text = False) :
        s = [u"    " * indent]
        if n is None :
            n = self.tree.getroot ()
        s.append (n.tag)
        for attr in sorted (n.attrib.keys ()) :
            s.append (u' %s="%s"' % (attr, n.attrib [attr]))
        if with_text :
            if n.text :
                s.append (u" TEXT: %s" % n.text)
            if n.tail :
                s.append (u" TAIL: %s" % n.tail)
        return ''.join (s).encode (self.charset)
    # end def as_string

    def tree_as_string (self, n = None, indent = 0, with_text = False) :
        if n is None :
            n = self.tree.getroot ()
        s = [self.as_string (n, indent = indent, with_text = with_text)]
        for sub in n :
            s.append \
                (self.tree_as_string (sub, indent + 1, with_text = with_text))
        return '\n'.join (s)
    # end def tree_as_string

    def parse (self) :
        raise NotImplementedError
    # end def parse
# end class Page_Tree
