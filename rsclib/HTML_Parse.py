#!/usr/bin/python2.4

import urllib
from   time                            import sleep
from   elementtidy.TidyHTMLTreeBuilder import TidyHTMLTreeBuilder
from   elementtree.ElementTree         import ElementTree
from   rsclib.autosuper                import autosuper
from   rsclib.Version                  import VERSION

namespace   = 'http://www.w3.org/1999/xhtml'

def tag (name) :
    return "{%s}%s" % (namespace, name)

def set_useragent (ua) :
    """ Set the useragent used for retrieving urls with urlopen """
    class AppURLopener (urllib.FancyURLopener) :
        version = ua
    urllib._urlopener = AppURLopener()
# end def set_useragent

translation = ''.join (chr (x) for x in range (256))

class Page_Tree (autosuper) :
    html_charset = 'latin1'
    delay   = 1
    retries = 10
    def __init__ \
        ( self
        , site         = None
        , url          = None
        , charset      = 'latin1'
        , verbose      = 0
        , html_charset = None
        , data         = None
        , ** kw
        ) :
        if site :
            self.site = site
        if url :
            self.url  = url
        self.url     = '/'.join ((self.site, self.url))
        self.charset = charset
        self.verbose = verbose
        self.retry   = 0
        if html_charset :
            self.html_charset = html_charset
        # By default avoid overloading a web-site
        if self.delay >= 1 :
            sleep (self.delay)
            set_useragent ('rsclib/HTML_Parse %s' % VERSION)
        args = []
        if data is not None :
            args = [data]
        f = None
        while not f and self.retry < self.retries :
            try :
                f = urllib.urlopen (self.url, *args)
                break
            except AttributeError :
                self.retry += 1
        text         = f.read ().translate (translation, '\0\015')
        builder      = TidyHTMLTreeBuilder (encoding = self.html_charset)
        builder.feed (text)
        self.tree    = ElementTree (builder.close ())
        self.parse ()
    # end def __init__

    def as_string (self, n = None, indent = 0, with_text = False) :
        """ Return given node (default root) as a string """
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
        """ Return tree starting at given node n (default root) to string """
        if n is None :
            n = self.tree.getroot ()
        s = [self.as_string (n, indent = indent, with_text = with_text)]
        for sub in n :
            s.append \
                (self.tree_as_string (sub, indent + 1, with_text = with_text))
        return '\n'.join (s)
    # end def tree_as_string

    def convert_to_html (self) :
        """ Convert current tree in place from xhtml to html """
        prefix = tag ('')
        length = len (prefix)
        for elem in self.tree.getiterator () :
            if elem.tag.startswith (prefix) :
                elem.tag = elem.tag [length:]
    # end def convert_to_html

    def get_text (self, node = None, strip = True) :
        """ Return all text below starting node n (default root) """
        if node is None :
            node = self.tree.getroot ()
        text = []
        if node.text :
            text.append (node.text)
        for n in node :
            text.append (self.get_text (n, strip = False))
        if node.tail :
            text.append (node.tail)
        text = ''.join (text)
        if strip :
            return text.strip ()
        return text
    # end def get_text

    def parse (self) :
        raise NotImplementedError
    # end def parse
# end class Page_Tree
