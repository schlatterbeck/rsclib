#!/usr/bin/python2.4

from os                              import unlink, fdopen, popen
from urllib                          import urlopen
from tempfile                        import mkstemp
from elementtree.ElementTree         import ElementTree
from elementtidy.TidyHTMLTreeBuilder import TidyHTMLTreeBuilder
from rsclib.HTML_Parse               import Page_Tree

class PDF_Tree (Page_Tree) :
    def __init__ \
        ( self
        , site = None
        , url = None
        , charset      = 'latin1'
        , verbose      = 0
        , html_charset = None
        , pdf_charset  = 'Latin1'
        ) :
        if site :
            self.site = site
        if url :
            self.url  = url
        self.url     = '/'.join ((self.site, self.url))
        self.charset = charset
        self.verbose = verbose
        text         = urlopen (self.url).read ()
        f, fname     = mkstemp ('.pdf')
        f            = fdopen (f, 'w')
        f.write (text)
        f.close ()
        if not html_charset :
            html_charset = pdf_charset.lower ()
        html         = popen \
            ('pdftotext -enc %s -htmlmeta %s -' % (pdf_charset, fname))
        builder      = TidyHTMLTreeBuilder (encoding = html_charset)
        builder.feed (html.read ())
        html.close ()
        self.tree    = ElementTree (builder.close ())
        unlink (fname)
        self.parse ()
    # end def __init__
# end class PDF_Tree
