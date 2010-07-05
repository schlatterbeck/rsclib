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

from   rsclib.autosuper                import autosuper

class ETree (autosuper) :
    """ Extend ElementTree with some useful stuff
    """
    def __init__ (self, etree, charset = 'utf-8') :
        self.etree   = etree
        self.charset = charset
    # end def __init__

    def as_string (self, n = None, indent = 0, with_text = False) :
        """ Return given node (default root) as a string """
        s = [u"    " * indent]
        if n is None :
            n = self.etree.getroot ()
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

    def __getattr__ (self, name) :
        """ Delegate everything to our ElementTree and cache the result """
        x = getattr (self.etree, name)
        setattr (self, name, x)
        return x
    # end def __getattr__ 

# end class ETree
