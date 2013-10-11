#!/usr/bin/python
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

from   __future__       import unicode_literals
from   rsclib.autosuper import autosuper
from   StringIO         import StringIO
try :
    from xml.etree.ElementTree   import ElementTree, Element, SubElement
except ImportError :
    from elementtree.ElementTree import ElementTree, Element, SubElement

def _walk (root, before = None, after = None) :
    """ Walk the tree starting at root, call method "before" before
        descending into child nodes and method "after" afterwards. Both
        methods won't be called if not callable.

        We iterate over a copy so that all children of root are reached.
    """
    for n, sub in enumerate (root [:]) :
        if callable (before) :
            before (root, sub)
        _walk (sub, before, after)
        if callable (after) :
            after (root, sub)
# end def _walk

class ETree (autosuper) :
    """ Extend ElementTree with some useful stuff
    """
    def __init__ (self, etree, charset = 'utf-8') :
        if not isinstance (etree, ElementTree) :
            etree = ElementTree (etree)
        self.etree   = etree
        self.charset = charset
    # end def __init__

    def as_string \
        ( self
        , n         = None
        , indent    = 0
        , with_text = False
        , with_attr = True
        , encode    = True
        ) :
        """ Return given node (default root) as a string """
        if encode and self.charset is None :
            encode = False
        s = [u"    " * indent]
        if n is None :
            n = self.etree.getroot ()
        s.append (n.tag)
        if with_attr :
            for attr in sorted (n.attrib.keys ()) :
                s.append (' %s="%s"' % (attr, n.attrib [attr]))
        if with_text :
            if n.text :
                s.append (" TEXT: %s" % n.text)
            if n.tail :
                s.append (" TAIL: %s" % n.tail)
        if encode :
            return ''.join (s).encode (self.charset)
        return ''.join (s)
    # end def as_string

    def as_xml (self) :
        """ Convenience wrapper to return XML as a string using
            ElementTree.write
        """
        s = StringIO ()
        self.write (s)
        r = s.getvalue ()
        s.close ()
        return r
    # end def as_xml

    def tree_as_string (self, n = None, indent = 0, with_text = False) :
        """ Return tree starting at given node n (default root) to string """
        if n is None :
            n = self.etree.getroot ()
        s = [self.as_string (n, indent = indent, with_text = with_text)]
        for sub in n :
            s.append \
                (self.tree_as_string (sub, indent + 1, with_text = with_text))
        return '\n'.join (s)
    # end def tree_as_string

    def get_text (self, node = None, strip = True) :
        """ Return all text below starting node (default root) """
        if node is None :
            node = self.etree.getroot ()
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

    def pretty (self, node = None, indent = 0, with_text = False) :
        """ Pretty printed XML, default to start at root node """
        if node is None :
            node = self.etree.getroot ()
        s = ['    ' * indent]
        if len (node) or with_text and node.text :
            s.append ("<%s>" % self.as_string (node))
            if len (node) :
                s.append ('\n')
            if with_text and node.text :
                if len (node) :
                    s.append ('    ' * indent)
                s.append (node.text.encode (self.charset))
                if len (node) :
                    s.append ('\n')
            for n in node :
                s.append (self.pretty (n, indent + 1, with_text))
            if len (node) :
                s.append ('    ' * indent)
            s.append ("</%s>\n" % self.as_string (node, with_attr = False))
        else :
            s.append ("<%s/>\n" % self.as_string (node))
        if with_text and node.tail :
            s.append (node.tail.encode (self.charset))
            s.append ('\n')
        return ''.join (s)
    # end def pretty

    def walk (self, before = None, after = None) :
        """ Walk the tree starting at root, call method "before" before
            descending into child nodes and method "after" afterwards.
            Both methods won't be called if not callable.

            We iterate over a copy so that all children of root are reached.
        """
        return _walk (self.getroot (), before, after)
    # end def walk

    def __getattr__ (self, name) :
        """ Delegate everything to our ElementTree and cache the result """
        x = getattr (self.etree, name)
        setattr (self, name, x)
        return x
    # end def __getattr__ 

# end class ETree
