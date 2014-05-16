#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__       import absolute_import
from __future__       import print_function
from __future__       import unicode_literals
from rsclib.pycompat  import ustr, string_types
try :
    from xml.etree.ElementTree   import ElementTree, Element, SubElement
except ImportError :
    from elementtree.ElementTree import ElementTree, Element, SubElement
from netrc            import netrc
from urllib           import urlencode
from urllib2          import urlopen, Request, HTTPError
from json             import load as jsonload, dumps as jsondumps

from rsclib.autosuper import autosuper
from rsclib.ETree     import ETree


class Freshmeat (autosuper) :
    url = "https://freecode.com/projects/%(project)s/%(objname)s.%(type)s"

    """ Class to get or put freshmeat.net (aka freecode.com) objects.
        Example is the list of releases for a specific project, see
        doctest of __init__
    """

    netrc_hosts = ('freecode.com', 'freshmeat.net')

    content_type = {'json' : 'application/json', 'xml' : 'text/xml'}

    def __init__ \
        ( self
        , project
        , objname
        , auth_code = None
        , put       = None
        , charset   = 'utf-8'
        , type      = 'json'
        ) :
        """
        >>> import sys
        >>> f = Freshmeat ('ooopy', 'releases', type = 'xml')
        >>> print (f.tree_as_string (f.getroot ()[-3]))
        release
            approved-at type="datetime"
            changelog
            created-at type="datetime"
            hidden-from-frontpage type="boolean"
            id type="integer"
            version
            tag-list
        >>> e = ElementTree (f.getroot ()[-3])
        >>> e.write (sys.stdout)
        <release>
            <approved-at type="datetime">2008-02-28T04:55:33Z</approved-at>
            <changelog>Small documentation changes.</changelog>
            <created-at type="datetime">2008-02-28T12:55:33Z</created-at>
            <hidden-from-frontpage type="boolean">false</hidden-from-frontpage>
            <id type="integer">272703</id>
            <version>1.1.4477</version>
            <tag-list>Minor bugfixes</tag-list>
          </release>
        <BLANKLINE>
        >>> f = Freshmeat ('ooopy', 'releases')
        >>> print (f.pretty (f.content [-3]))
        release:
            changelog: 'Small documentation changes.'
            created_at: '2008-02-28T12:55:33Z'
            version: '1.1.4477'
            hidden_from_frontpage: False
            tag_list:
                LIST:
                    'Minor bugfixes'
            approved_at: '2008-02-28T04:55:33Z'
            id: 272703
        >>> f = Freshmeat ('ooopy', 'releases/%s' % 272703, type = 'xml')
        >>> f.write (sys.stdout)
        <release>
          <approved-at type="datetime">2008-02-28T04:55:33Z</approved-at>
          <changelog>Small documentation changes.</changelog>
          <created-at type="datetime">2008-02-28T12:55:33Z</created-at>
          <hidden-from-frontpage type="boolean">false</hidden-from-frontpage>
          <id type="integer">272703</id>
          <version>1.1.4477</version>
          <tag-list>Minor bugfixes</tag-list>
        </release>
        >>> f = Freshmeat ('ooopy', 'releases/%s' % 272703)
        >>> print (f.pretty ())
        release:
            changelog: 'Small documentation changes.'
            created_at: '2008-02-28T12:55:33Z'
            version: '1.1.4477'
            hidden_from_frontpage: False
            tag_list:
                LIST:
                    'Minor bugfixes'
            approved_at: '2008-02-28T04:55:33Z'
            id: 272703
        >>> r = Release ('1.2.3', 'something changed', False, 'bugfix')
        >>> r.json
        '{"changelog": "something changed", "version": "1.2.3", "tag_list": ["bugfix"], "hidden_from_frontpage": false}'
        >>> url = "http://localhost/%(project)s/%(objname)s.%(type)s"
        >>> Freshmeat.url = url
        >>> f = Freshmeat ('ooopy', 'releases', put = r, type = 'xml')
        >>> print (f.code, f.result)
        404 Not Found
        >>> f = Freshmeat ('ooopy', 'releases', put = r)
        >>> print (f.code, f.result)
        404 Not Found
        """
        self.project   = project
        self.objname   = objname
        self.charset   = charset
        self.type      = type
        self.c_type    = self.content_type [type]
        self.url       = self.url % locals ()
        self.auth_code = auth_code or self.get_auth ()
        self.code      = None
        self.result    = None
        self.content   = None
        if put :
            self.content = self._put (put)
        else :
            self.content = self._get ()
    # end def __init__

    def _get (self) :
        r    = Request (self.url + '?auth_code=%s' % self.auth_code)
        f = urlopen (r)
        if self.type == 'xml' :
            return ETree (ElementTree (file = f))
        return jsonload (f)
    # end def _get

    def _put (self, putobj) :
        auth = '?auth_code=%s' % self.auth_code
        if self.type == 'xml' :
            tree = ETree (putobj.element)
            data = tree.as_xml ()
        else :
            auth = ''
            data = dict (auth_code = self.auth_code, release = putobj.content)
            data = jsondumps (data)
        r = Request (self.url + auth, data)
        r.add_header \
            ( 'Content-Type'
            , '%(c_type)s; charset=%(charset)s'
            % self.__dict__
            )
        try :
            f = urlopen (r)
            if self.type == 'xml' :
                return ETree (ElementTree (file = f))
            return jsonload (f)
        except HTTPError as cause :
            self.code   = cause.code
            self.result = cause.msg
            self.err    = cause.readlines ()
    # end def _put

    def get_auth (self, netrc_file = None, netrc_hosts = None) :
        netrc_hosts = netrc_hosts or self.netrc_hosts
        n = netrc (netrc_file)
        for h in netrc_hosts :
            auth = n.authenticators (h)
            if auth :
                return auth [2]
    # end def get_auth

    def pretty (self, item = None, ident = 0, ** kw) :
        if item is None :
            item = self.content
        if isinstance (item, ETree) :
            return item.pretty (** kw)
        else :
            ws = '    ' * ident
            r  = []
            if isinstance (item, list) :
                r.append ('%sLIST:' % ws)
                for k in item :
                    r.append (self.pretty (k, ident + 1))
            elif isinstance (item, dict) :
                for k, v in item.iteritems () :
                    if not isinstance (v, (list, dict)) :
                        if isinstance (v, string_types) :
                            v = ustr (v)
                        r.append ("%s%s: %r" % (ws, k, v))
                    else :
                        r.append ("%s%s:" % (ws, k))
                        r.append (self.pretty (v, ident + 1))
            else :
                if isinstance (item, string_types) :
                    item = ustr (item)
                r.append ("%s%r" % (ws, ustr (item)))
        return '\n'.join (r)
    # end def pretty

    def __getattr__ (self, name) :
        """ Delegate to self.content """
        if self.type == 'xml' :
            if name == 'content' :
                raise AttributeError ('Our content attribute vanished')
            v = getattr (self.content, name)
            setattr (self, name, v)
            return v
        raise AttributeError (name)
    # end def __getattr__

# end class Freshmeat

class Release (autosuper) :

    def __init__ (self, version, changelog, hidden = False, *tags) :
        """
        >>> import sys
        >>> r = Release ('1.2.3', 'something changed', False, 'bugfix')
        >>> e = ETree (ElementTree (r.element))
        >>> print (e.tree_as_string ())
        release
            changelog
            hidden-from-frontpage type="boolean"
            version
            tag-list
        >>> print (e.pretty (with_text = True))
        <release>
            <changelog>something changed</changelog>
            <hidden-from-frontpage type="boolean">false</hidden-from-frontpage>
            <version>1.2.3</version>
            <tag-list>bugfix</tag-list>
        </release>
        <BLANKLINE>
        >>> print (r.json)
        {"changelog": "something changed", "version": "1.2.3", "tag_list": ["bugfix"], "hidden_from_frontpage": false}
        """
        self.changelog = changelog
        self.hidden    = hidden
        self.version   = version
        self.tags      = tags
        self._element  = None
        self._json     = None
        self._content  = None
    # end def __init__

    @property
    def element (self) :
        if not self._element :
            r = Element ('release')
            c = SubElement (r, 'changelog')
            c.text = self.changelog
            h = SubElement (r, 'hidden-from-frontpage', type = 'boolean')
            h.text = str (self.hidden).lower ()
            v = SubElement (r, 'version')
            v.text = self.version
            if self.tags :
                t = SubElement (r, 'tag-list')
                t.text = ','.join (self.tags)
            self._element = r
        return self._element
    # end def element

    @property
    def content (self) :
        if not self._content :
            self._content = d = dict \
                ( hidden_from_frontpage = bool (self.hidden)
                , version               = self.version
                , changelog             = self.changelog
                )
            if self.tags :
                d ['tag_list'] = list (self.tags)
        return self._content
    # end def content

    @property
    def json (self) :
        if not self._json :
            self._json = jsondumps (self.content)
        return self._json
    # end def json

# end class Release
