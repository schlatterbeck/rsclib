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

from os                              import unlink, fdopen, popen
from urllib                          import urlopen
from tempfile                        import mkstemp
try :
    from xml.etree.ElementTree import ElementTree
except ImportError :
    from elementtree.ElementTree import ElementTree
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
