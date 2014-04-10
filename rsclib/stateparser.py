#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
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

from __future__          import unicode_literals

import re
import sys
from rsclib.autosuper    import autosuper
from rsclib.base_pickler import Base_Pickler
from rsclib.pycompat     import string_types

class Parse_Error (ValueError) : pass

class Debug (autosuper) :
    def debug (self, level, * msg) :
        if self.verbose >= level :
            print >> sys.stderr, ' '.join (unicode (x) for x in msg)
            sys.stderr.flush ()
    # end def debug
# end class Debug

class Transition (Debug) :
    """ Represents one line in a state-change diagram. If matched,
        applies the defined action (if any) and returns new state.

        A match can be either None (which matches everything), a string
        (which matches if it is identical to the matched token) or a
        regular expression.

        Action methods get the matched line, and in case of a regex the
        matched groups as parameter.
    """
    def __init__ (self, pattern, state, new_state, action, **kw) :
        self.pattern   = pattern
        self.state     = state
        self.new_state = new_state
        self.verbose   = kw.get ('verbose')
        self.act_name  = action
        if action :
            action = getattr (self.state.parser, action)
        self.action    = action
        self.__super.__init__ (**kw)
    # end def __init__

    def _transition (self, match = None) :
        new    = None
        pstate = self.state.parser.state
        line   = self.state.parser.line
        if self.action :
            new = self.action (self.state, self.new_state, match)
        new    = new or self.new_state
        self.debug \
            ( 1
            , "state: %s new: %s call: %s match: %r"
            % (pstate.name, new.name, self.act_name, line)
            )
        return new
    # end def _transition

    def match (self) :
        line = self.state.parser.line
        if self.pattern is None or line == self.pattern :
            self.debug \
                (2, "match: %s (act = %s)" % (self.pattern, self.act_name))
            return self._transition ()
        if not isinstance (self.pattern, string_types) :
            m = self.pattern.search (line)
            if m :
                self.debug (2, "match: <regex> (act = %s)" % self.act_name)
                return self._transition (m)
        self.debug \
            ( 4
            , "state: %s: No match: %r (act = %s)"
              % (self.state.name, line, self.act_name)
            )
        return None
    # end def match

# end class Transition

class State (Debug) :
    """ Represents a single state of the parser """

    def __init__ (self, parser, name, **kw) :
        self.name        = name
        self.parser      = parser
        self.transitions = []
        self.verbose     = kw.get ('verbose')
        self.__super.__init__ (**kw)
    # end def __init__

    def append (self, transition) :
        self.transitions.append (transition)
    # end def append

    def match (self) :
        for t in self.transitions :
            state = t.match ()
            if state :
                return state
        else :
            raise Parse_Error, "%s: %s" % (self.parser.lineno, self.parser.line)
    # end def match

# end class State

class Parser (Debug, Base_Pickler) :
    """ Simple state-machine parser.
        To use, define a subclass with the necessary actions. An action
        method gets the line matched and an optional match object.
    """

    pickle_exceptions = dict.fromkeys (('stack', 'state', 'states'))
    encoding          = 'latin1'

    def __init__ (self, matrix = None, **kw) :
        self.verbose = kw.get ('verbose')
        self.state   = None
        self.states  = {}
        matrix = matrix or self.matrix
        self.__super.__init__ (**kw)
        for line in matrix :
            self.add_transition (* line)
        self.stack   = []
    # end def __init__

    def add_transition (self, statename, pattern, newname, action) :
        if statename not in self.states :
            self.states [statename] = \
                State (self, statename, verbose = self.verbose)
        state = self.states [statename]
        new   = None
        if newname :
            if newname not in self.states :
                self.states [newname] = \
                    State (self, newname, verbose = self.verbose)
            new = self.states [newname]
        if not self.state :
            self.state = state
        t = Transition \
            (pattern, state, new, action, verbose = self.verbose)
        state.append (t)
    # end def add_transition

    def parse (self, file) :
        for n, line in enumerate (file) :
            if self.encoding :
                line = line.decode (self.encoding)
            self.line   = line.rstrip ()
            self.lineno = n + 1
            try :
                self.state  = self.state.match ()
            except StandardError, cause :
                #raise Parse_Error, (self.lineno, cause)
                raise
    # end def parse

    def push (self, state, new_state = None, match = None) :
        self.stack.append (state)
        stack = [s.name for s in self.stack]
        self.debug (3, "push: %s, stack: %s" % (new_state.name, stack))
    # end def push
    
    def pop (self, state = None, new_state = None, match = None) :
        self.debug \
            ( 3
            , "before pop: %s" % self.state.name
            , "stack:"
            , [s.name for s in self.stack]
            )
        state = self.stack.pop ()
        self.debug \
            ( 3
            , "after  pop: %s" % state.name
            , "stack:"
            , [s.name for s in self.stack]
            )
        self.debug (3, "stack:", [s.name for s in self.stack])
        state = state.match ()
        return state
    # end def pop
# end class Parser

