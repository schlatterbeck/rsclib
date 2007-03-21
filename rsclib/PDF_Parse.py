#!/usr/bin/python2.4

from os                import unlink
from urllib            import urlopen
from StringIO          import StringIO
from tempfile          import mkstemp
from rsclib.HTML_Parse import Page_Tree

class PDF_Tree (Page_Tree) :
    def __init__ (self, site, url, charset = 'Latin1', verbose = 0) :
        self.site    = site
        self.url     = '/'.join ((site, url))
        self.charset = charset
        self.verbose = verbose
        text         = urlopen (self.url).read ()
        f, fname     = mkstemp ('.pdf')
        f.write (text)
        f.close ()
        html         = os.popen \
            ('pdftotext -enc %s -htmlmeta %s -' % (charset, fname))
        self.tree    = TidyHTMLTreeBuilder.parse (html)
        unlink (fname)
        self.parse ()
    # end def __init__
# end class PDF_Tree
