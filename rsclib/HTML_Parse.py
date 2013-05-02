#!/usr/bin/python
# Copyright (C) 2006-10 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import urllib2
import cookielib
from   time                            import sleep
from   elementtidy.TidyHTMLTreeBuilder import TidyHTMLTreeBuilder
try :
    from xml.etree.ElementTree import ElementTree
except ImportError :
    from elementtree.ElementTree import ElementTree
from   rsclib.base_pickler             import Base_Pickler
from   rsclib.Version                  import VERSION
from   rsclib.multipart_form           import Multipart_Form
from   rsclib.ETree                    import ETree
from   urllib                          import urlencode
from   httplib                         import BadStatusLine

namespace   = 'http://www.w3.org/1999/xhtml'

def tag (name) :
    return "{%s}%s" % (namespace, name)

def set_useragent (ua) :
    """ Set the useragent used for retrieving urls with urlopen2
        Deprecated: Use
        pt = Page_Tree
        pt.set_useragent (ua)
        instead
    """
    Page_Tree.headers ['User-Agent'] = ua
# end def set_useragent

class Retry            (ValueError)   : pass
class Retries_Exceeded (RuntimeError) : pass

translation = ''.join (chr (x) for x in range (256))
def default_translate (x) :
    return x.translate (translation, '\0\015')
# end def default_translate

class Page_Tree (Base_Pickler) :
    """ Parse given URL into an Elementtree (using ElementTidy).

        - site is the first part of an uri, e.g. http://example.com.
        - url  is the rest of the uri.
        - data is sent as a post request.
        - post is a dictionary converted to data suitable as a post
             request, if data is specified, post is ignored.
        - files are converted to file upload data in a post request
             if data is specified, files is ignored, files specifies
             tuples of the form (fieldname, filename, filehandle, mimetype)
             where the filehandle is an open file or None (in which case
             filename is opened).
        - if username and password are specified we use simplte http auth
        - cookies is a cookiejar object

        The parse method can be overridden to compute something from
        the elementtree in self.tree.
    """
    html_charset = 'latin1'
    delay   = 1
    retries = 10
    headers = {}
    pickle_exceptions = dict.fromkeys (('tree', 'pageinfo', 'cookies'))

    def __init__ \
        ( self
        , site         = None
        , url          = None
        , charset      = 'latin1'
        , verbose      = 0
        , html_charset = None
        , data         = None
        , post         = None
        , files        = None
        , username     = None
        , password     = None
        , cookies      = None
        , translate    = None
        , timeout      = None
        , ** kw
        ) :
        if site :
            self.site = site
        if url :
            self.url  = url
        if self.url is not None :
            self.url = '/'.join ((self.site, self.url))
        else :
            self.url = self.site
        self.charset = charset
        self.verbose = verbose
        self.retry   = 0
        self.timeout = timeout
        self.headers = self.headers # copy from class
        if html_charset :
            self.html_charset = html_charset
        # By default avoid overloading a web-site
        if self.delay >= 1 :
            sleep (self.delay)
            set_useragent ('rsclib/HTML_Parse %s' % VERSION)
        if not cookies :
            self.cookies = cookielib.LWPCookieJar ()
        else :
            self.cookies = cookies
        if not translate :
            translate = default_translate
        op = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))
        if username and password :
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm ()
            password_mgr.add_password (None, self.site, username, password)
            handler = urllib2.HTTPBasicAuthHandler (password_mgr)
            op.add_handler (handler)
        if not data :
            if files :
                form = Multipart_Form ()
                if post :
                    iter = post
                    if isinstance (post, dict) :
                        iter = dict.itervalues
                    for k, v in iter :
                        form.add_field (k, v)
                for fieldname, filename, filehandle, mimetype in files :
                    if not filehandle :
                        filehandle = open (filename, 'r')
                    form.add_file (fieldname, filename, filehandle, mimetype)
                data = str (form)
                self.headers ['Content-type']   = form.get_content_type ()
                self.headers ['Content-length'] = len (data)
            elif post :
                data = urlencode (post)
        rq = urllib2.Request (self.url, data, self.headers)
        f  = None
        while not f and self.retry < self.retries :
            try :
                f = op.open (rq, timeout = self.timeout) # urlopen
                self.pageurl  = f.geturl ()
                self.pageinfo = f.info ()
            except (AttributeError, urllib2.URLError, BadStatusLine) :
                self.retry += 1
                continue
            text      = translate (f.read ())
            builder   = TidyHTMLTreeBuilder (encoding = self.html_charset)
            builder.feed (text)
            self.tree = ETree \
                (ElementTree (builder.close ()), charset = charset)
            try :
                self.parse ()
            except Retry :
                f = None
                self.retry += 1
                continue
        if self.retry >= self.retries :
            raise Retries_Exceeded, (self.retries, self.url)
    # end def __init__

    def as_string (self, n = None, indent = 0, with_text = False) :
        """ Return given node (default root) as a string """
        return self.tree.as_string (n, indent, with_text)
    # end def as_string

    def tree_as_string (self, n = None, indent = 0, with_text = False) :
        """ Return tree starting at given node n (default root) to string """
        return self.tree.tree_as_string (n, indent, with_text)
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
        return self.tree.get_text (node, strip)
    # end def get_text

    def parse (self) :
        """ If you want to do more here, this should be overridden in a
            derived class.

            You may raise a Retry Exception in which case the page will
            be re-fetched. This comes in handy when pages have an access
            limit and this is detected by the parser. Note that you
            *should* pause for some time *before* raising Retry in that
            case.
        """
        pass
    # end def parse

    def set_header (self, key, val) :
        self.headers [key] = val
    # end def set_header

    def set_useragent (self, ua) :
        self.set_header ('User-Agent', ua)
    # end def set_useragent

# end class Page_Tree
