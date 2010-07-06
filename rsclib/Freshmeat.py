#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010 Dr. Ralf Schlatterbeck Open Source Consulting.
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

try :
    from xml.etree.ElementTree   import ElementTree, Element, SubElement
except ImportError :
    from elementtree.ElementTree import ElementTree, Element, SubElement
from netrc   import netrc
from urllib  import urlencode
from urllib2 import urlopen, Request

from rsclib.autosuper import autosuper
from rsclib.ETree     import ETree

class Get_Request_With_Data (Request) :
    """ This is a normal urllib2 Request but it will always use the
        "GET" method even when used with data (normal urllib2 Request
        will always use "POST" in that case). This is needed for
        freshmeats REST API.
    """
    def get_method (self) :
        return 'GET'
    # end def get_method
# end class Get_Request_With_Data

class Put_Request_With_Data (Request) :
    """ This is a normal urllib2 Request but it will always use the
        "PUT" method even when used with data (normal urllib2 Request
        will always use "POST" in that case). This is needed for
        freshmeats REST API.
    """
    def get_method (self) :
        return 'PUT'
    # end def get_method
# end class Put_Request_With_Data

class Freshmeat_Object (ETree) :
    url = "http://freshmeat.net/projects/%(project)s/%(objname)s.xml"

    """ Class the get or put freshmeat objects.
        Example is the list of releases for a specific project, e.g.
    """

    def __init__ \
        ( self
        , project
        , objname
        , auth_code = None
        , put       = None
        , charset   = 'utf-8'
        ) :
        """
        >>> import sys
        >>> f = Freshmeat_Object ('ooopy', 'releases')
        >>> print f.tree_as_string (f.getroot ()[-3])
        release
            approved-at type="datetime"
            changelog
            hidden-from-frontpage type="boolean"
            id type="integer"
            version
            tag-list
        >>> e = ElementTree (f.getroot ()[-3])
        >>> e.write (sys.stdout)
        <release>
            <approved-at type="datetime">2008-02-28T04:55:33Z</approved-at>
            <changelog>Small documentation changes.</changelog>
            <hidden-from-frontpage type="boolean">false</hidden-from-frontpage>
            <id type="integer">272703</id>
            <version>1.1.4477</version>
            <tag-list>Minor bugfixes</tag-list>
          </release>
        <BLANKLINE>
        >>> f = Freshmeat_Object ('ooopy', 'releases/%s' % '272703')
        >>> f.write (sys.stdout)
        <release>
          <approved-at type="datetime">2008-02-28T04:55:33Z</approved-at>
          <changelog>Small documentation changes.</changelog>
          <hidden-from-frontpage type="boolean">false</hidden-from-frontpage>
          <id type="integer">272703</id>
          <version>1.1.4477</version>
          <tag-list>Minor bugfixes</tag-list>
        </release>
        >>> r = Release ('1.2.3', 'something changed', False, 'bugfix')
        >>> url = "http://localhost/%(project)s/%(objname)s.xml"
        >>> Freshmeat_Object.url = url
        >>> f = Freshmeat_Object ('ooopy', 'releases', put = r.element)
        Traceback (most recent call last):
        HTTPError: HTTP Error 405: Method Not Allowed
        """
        self.project   = project
        self.objname   = objname
        self.charset   = charset
        self.url       = self.url % locals ()
        self.auth_code = auth_code or self.get_auth ()
        if put :
            self.__super.__init__ (self._put (put))
        else :
            self.__super.__init__ (self._get ())
    # end def from_file

    def _get (self) :
        data = urlencode (dict (auth_code = self.auth_code))
        r    = Get_Request_With_Data (self.url, data)
        f = urlopen (r)
        return ElementTree (file = f)
    # end def _get

    def _put (self, putobj) :
        self.url = 'http://localhost'
        e = Element ('releases')
        e.append (putobj)
        data = ETree (e).as_xml ()
        r = Put_Request_With_Data (self.url, data)
        r.add_header ('Content-Type', 'text/xml; charset=%s' % self.charset)
        f = urlopen (r)
        self.result = f.read ()
        return ElementTree (e)
    # end def _put

    def get_auth (self, netrc_file = None, netrc_host = 'freshmeat.net') :
        n = netrc (netrc_file)
        return n.authenticators (netrc_host)[2]
    # end def get_auth
# end class Freshmeat_Object

class Release (autosuper) :
    def __init__ (self, version, changelog, hidden = False, *tags) :
        """
        >>> import sys
        >>> r = Release ('1.2.3', 'something changed', False, 'bugfix')
        >>> e = ETree (ElementTree (r.element))
        >>> print e.tree_as_string ()
        release
            changelog
            hidden-from-frontpage type="boolean"
            version
            tag-list
        >>> print e.pretty (with_text = True)
        <release>
            <changelog>something changed</changelog>
            <hidden-from-frontpage type="boolean">false</hidden-from-frontpage>
            <version>1.2.3</version>
            <tag-list>bugfix</tag-list>
        </release>
        <BLANKLINE>
        """
        r = Element ('release')
        c = SubElement (r, 'changelog')
        c.text = changelog
        h = SubElement (r, 'hidden-from-frontpage', type = 'boolean')
        h.text = str (hidden).lower ()
        v = SubElement (r, 'version')
        v.text = version
        if tags :
            t = SubElement (r, 'tag-list')
            t.text = ','.join (tags)
        self.element = r
    # end def __init__
# end class Release

#class Freshmeat (autosuper) :
#    def __init__ (self, project) :
#        self.project = project
#        
#        ooopy/releases.xml
#    # end def __init__
#
#    def post_release (self, auth_code, release) :
#        url = self.url + 'releases.xml'
#    # end def post_release
## end class Freshmeat

#<release>
#<approved-at type="datetime">2008-06-03T12:51:40Z</approved-at>
#<changelog>Doctest was fixed to hopefully run on Windows.</changelog>
#<hidden-from-frontpage type="boolean">true</hidden-from-frontpage>
#<id type="integer">278892</id>
#<version>1.4.4873</version>
#<tag-list>Minor bugfixes</tag-list>
#</release>
