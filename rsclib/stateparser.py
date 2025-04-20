#!/usr/bin/python3
# Copyright (C) 2007-24 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ****************************************************************************

from __future__          import unicode_literals, print_function

import re
import sys
from rsclib.autosuper    import autosuper
from rsclib.base_pickler import Base_Pickler
from rsclib.pycompat     import string_types, text_type

pattern_type = type (re.compile (''))

class Parse_Error (ValueError): pass

class Debug (autosuper):
    def debug (self, level, * msg):
        if self.debug_level >= level:
            print (' '.join (text_type (x) for x in msg), file = sys.stderr)
            sys.stderr.flush ()
    # end def debug
# end class Debug

class Transition (Debug):
    """ Represents one line in a state-change diagram. If matched,
        applies the defined action (if any) and returns new state.

        A match can be either None (which matches everything), a string
        (which matches if it is identical to the matched token) or a
        regular expression.

        Action methods get the matched line, and in case of a regex the
        matched groups as parameter.
    """
    def __init__ (self, pattern, state, new_state, action, **kw):
        self.pattern     = pattern
        self.state       = state
        self.new_state   = new_state
        self.debug_level = kw.get ('debug_level', 0)
        self.act_name    = action
        if action:
            action = getattr (self.state.parser, action)
        self.action      = action
        self.__super.__init__ (**kw)
    # end def __init__

    def _transition (self, match = None):
        new    = None
        pstate = self.state.parser.state
        line   = self.state.parser.line
        if self.action:
            new = self.action (self.state, self.new_state, match)
        new    = new or self.new_state
        self.debug \
            ( 1
            , "state: %s new: %s call: %s match: %r"
            % (pstate.name, new.name, self.act_name, line)
            )
        return new
    # end def _transition

    def match (self):
        line = self.state.parser.line
        if self.pattern is None or line == self.pattern:
            self.debug \
                (2, "match: %s (act = %s)" % (self.pattern, self.act_name))
            return self._transition ()
        if isinstance (self.pattern, pattern_type):
            m = self.pattern.search (line)
            if m:
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

class State (Debug):
    """ Represents a single state of the parser """

    def __init__ (self, parser, name, **kw):
        self.name        = name
        self.parser      = parser
        self.transitions = []
        self.debug_level = kw.get ('debug_level', 0)
        self.__super.__init__ (**kw)
    # end def __init__

    def append (self, transition):
        self.transitions.append (transition)
    # end def append

    def match (self):
        for t in self.transitions:
            state = t.match ()
            if state:
                return state
        else:
            raise Parse_Error \
                ("%s: %s" % (self.parser.lineno, self.parser.line))
    # end def match

# end class State

class Parser (Debug, Base_Pickler):
    """ Simple state-machine parser.
        To use, define a subclass with the necessary actions. An action
        method gets the line matched and an optional match object.
    """

    pickle_exceptions = dict.fromkeys (('stack', 'state', 'states'))
    encoding          = 'latin1'

    def __init__ (self, matrix = None, **kw):
        self.debug_level = kw.get ('debug_level', 0)
        self.state       = None
        self.states      = {}
        matrix = matrix or self.matrix
        self.__super.__init__ (**kw)
        for line in matrix:
            self.add_transition (* line)
        self.stack   = []
    # end def __init__

    def add_transition (self, statename, pattern, newname, action):
        if statename not in self.states:
            self.states [statename] = \
                State (self, statename, debug_level = self.debug_level)
        state = self.states [statename]
        new   = None
        if newname:
            if newname not in self.states:
                self.states [newname] = \
                    State (self, newname, debug_level = self.debug_level)
            new = self.states [newname]
        if not self.state:
            self.state = state
        t = Transition \
            (pattern, state, new, action, debug_level = self.debug_level)
        state.append (t)
    # end def add_transition

    def parse (self, file):
        for n, line in enumerate (file):
            if self.encoding:
                line = line.decode (self.encoding)
            self.line   = line.rstrip ()
            self.lineno = n + 1
            try:
                self.state  = self.state.match ()
            except Exception as cause:
                #raise Parse_Error (self.lineno, cause)
                raise
    # end def parse

    def push (self, state, new_state = None, match = None):
        self.stack.append (state)
        stack = [s.name for s in self.stack]
        self.debug (3, "push: %s, stack: %s" % (new_state.name, stack))
    # end def push

    def pop (self, state = None, new_state = None, match = None):
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

    def endpop (self, state = None, new_state = None, match = None):
        """ Pop stack *after* handling the current line
        """
        return self.stack.pop ()
    # end def endpop
# end class Parser

