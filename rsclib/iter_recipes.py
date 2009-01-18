#!/usr/bin/python
# Copyright (C) 2009 Dr. Ralf Schlatterbeck Open Source Consulting.
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

# Some recipes for iterating, some from
# http://docs.python.org/library/itertools.html

from itertools import izip, tee

def grouper (n, iterable) :
    """
        >>> list (grouper (3, 'ABCDEFG'))
        [('A', 'B', 'C'), ('D', 'E', 'F')]
    """
    args = [iter (iterable)] * n
    return izip (*args)
# end def grouper

def pairwise (iterable) :
    """
        >>> list (pairwise (["s0", "s1", "s2", "s3"]))
        [('s0', 's1'), ('s1', 's2'), ('s2', 's3')]
    """
    a, b = tee (iterable)
    for elem in b :
        break
    return izip (a, b)
# end def pairwise

def ranges (iterable, key = None, condition = None) :
    """ Convert adjacent items in iterable to a list of ranges.
        The key, if present, will convert the items to numbers where adjacent items differ
        by on (e.g. for internet addresses). The optional condition tests each pair, only
        if the condition evaluates to True is the pair considered ajacent.
        >>> tuple (ranges ((1,2,3,4,5,9,10,11,21)))
        ((1, 5), (9, 11), (21, 21))
        >>> tuple (ranges ((1,2,3,4,5,9,10,11,21,22)))
        ((1, 5), (9, 11), (21, 22))
        >>> tuple (ranges ((1,2,4,5,9,10,11,21,22)))
        ((1, 2), (4, 5), (9, 11), (21, 22))
        >>> tuple (ranges ((1,)))
        ((1, 1),)
    """
    if not key :
        key = lambda x : x
    first = last = None
    i1, i2 = tee (iterable)
    try :
        last = i1.next ()
    except StopIteration :
        pass
    for x1, x2 in pairwise (i2) :
        last = x2
        if key (x1) + 1 == key (x2) and (not condition or condition (x1, x2)) :
            if not first :
                first = x1
            continue
        if first :
            yield (first, x1)
            first = None
        else :
            yield (x1, x1)
    if last :
        if first :
            yield (first, last)
            first = None
        else :
            yield (last, last)
# end def ranges
