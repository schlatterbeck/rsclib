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
        The key, if present, will convert the items to numbers where
        adjacent items differ by one (e.g. for internet addresses). The
        optional condition tests each pair, only if the condition
        evaluates to True is the pair considered ajacent.
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

def xxrange (start, stop = None, step = 1) :
    """ Reimplementation of xrange that works for x-large numbers,
        native xrange doesn't work with long integers. Note that we
        enforce the same restriction as native xrange, we don't allow
        float.
        >>> list (xrange (8))
        [0, 1, 2, 3, 4, 5, 6, 7]
        >>> list (xxrange (8))
        [0L, 1L, 2L, 3L, 4L, 5L, 6L, 7L]
        >>> list (xrange (6, 8))
        [6, 7]
        >>> list (xxrange (6, 8))
        [6L, 7L]
        >>> list (xrange (2, 8, 2))
        [2, 4, 6]
        >>> list (xxrange (2, 8, 2))
        [2L, 4L, 6L]
        >>> 0x800000000000
        140737488355328L
        >>> 0x800000000000 + 0x400000000000
        211106232532992L
        >>> list (xxrange (0x800000000000, 0x1000000000000, 0x400000000000))
        [140737488355328L, 211106232532992L]
        >>> list (xrange(8, 6, -1))
        [8, 7]
        >>> list (xxrange(8, 6, -1))
        [8L, 7L]
        >>> list (xrange(8, 9, -1))
        []
        >>> list (xxrange(8, 9, -1))
        []
        >>> list (xxrange(8, 9, 0))
        Traceback (most recent call last):
          ...
        ValueError: xxrange arg 3 must not be zero
        >>> list (xxrange(8, 9, 0.25))
        Traceback (most recent call last):
          ...
        ValueError: xxrange arg 3 must not be zero
        >>> list (xxrange (8.5, 9.5, 1))
        [8L]
    """
    if stop is None :
        stop  = start
        start = 0
    step  = long (step)
    start = long (start)
    stop  = long (stop)
    if step == 0 :
        raise ValueError ("xxrange arg 3 must not be zero")
    if step > 0 :
        while start < stop :
            yield start
            start += step
    else :
        while start > stop :
            yield start
            start += step
# end def xxrange

try :
    from itertools import combinations
except ImportError :
    def combinations (iterable, r) :
        """ stolen from python2.6 manpage of itertools:
        >>> tuple (tuple (i) for i in combinations ('ABCD', 2))
        (('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D'), ('C', 'D'))
        >>> tuple (tuple (i) for i in combinations (range (4), 3))
        ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
        """
        pool = tuple (iterable)
        n = len (pool)
        if r > n :
            return
        indices = range (r)
        yield tuple (pool [i] for i in indices)
        while True:
            for i in reversed (range (r)) :
                if indices [i] != i + n - r:
                    break
            else:
                return
            indices [i] += 1
            for j in range (i+1, r) :
                indices [j] = indices [j-1] + 1
            yield tuple (pool [i] for i in indices)
