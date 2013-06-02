#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
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

import os
import sys
import logging
import errno
import signal
import atexit
from   logging.handlers import SysLogHandler
from   traceback        import format_exc
from   subprocess       import Popen, PIPE
from   rsclib.autosuper import autosuper

class Exec_Error    (RuntimeError) : pass

class _Named (autosuper) :
    @property
    def clsname (self) :
        return self.__class__.__name__.lower ().replace ('_', '-')
    # end def clsname
# end class _Named

class Log (_Named) :
    """ Logger mixin. Sets up a log prefix automagically but can take
        arguments for setting log_level and log_prefix.
        Use as self.log.debug (msg), self.log.info (msg) etc.
    """
    logprefix = ''
    def __init__ (self, log_level = None, log_prefix = None, *args, **kw) :
        log_prefix = log_prefix or '%s%s' % (self.logprefix, self.clsname)
        self.log_prefix = log_prefix
        self.log        = logging.getLogger (log_prefix)
        if not len (self.log.handlers) :
            log_level  = log_level or logging.DEBUG
            formatter  = logging.Formatter \
                ('%s[%%(process)d]: %%(message)s' % log_prefix)
            handler    = SysLogHandler ('/dev/log', 'daemon')
            handler.setLevel     (log_level)
            handler.setFormatter (formatter)
            self.log.addHandler  (handler)
            self.log.setLevel    (log_level)
        self.__super.__init__ (*args, **kw)
    # end def __init__

    def log_exception (self) :
        for l in format_exc ().split ('\n') :
            if l :
                self.log.error (l)
    # end def log_exception

    def print_exception (self) :
        for l in format_exc ().split ('\n') :
            if l :
                print "%s\r" % l
    # end def print_exception
# end class Log

class Exec (Log) :
    def error (self, msg) :
        """ Just print error here, a derived class may want to do
            cleanup actions.
        """
        self.log.error (msg)
    # end def error

    def exec_pipe \
        ( self, args, stdin = None, ignore_err = False, shell = False) :
        popen_stdin = None
        if stdin is not None :
            popen_stdin = PIPE
        p = Popen \
            ( args
            , stdin  = popen_stdin
            , stdout = PIPE
            , stderr = PIPE
            , shell  = shell
            )
        stdout, stderr = p.communicate (stdin)
        self.stderr = err = ' '.join (stderr.rstrip ().split ('\n'))
        if p.returncode != 0 :
            arg = args [0]
            if shell :
                arg = args
            msg = "Nonzero exitcode %s from %s: %s" % (p.returncode, arg, err)
            self.error (msg)
            for e in stderr.rstrip ().split ('\n') :
                self.error (e)
            if not ignore_err :
                raise Exec_Error, (msg, p.returncode)
        return stdout.rstrip ().split ('\n')
    # end def exec_pipe
# end class Exec

class Lock_Mixin (_Named) :
    def __init__ (self, *args, **kw) :
        self.need_unlock = True
        self.__super.__init__ (*args, **kw)
        self.lockfile = '/var/lock/%s.lock' % self.clsname
        atexit.register (self.unlock)
        try :
            fd = os.open (self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            f  = os.fdopen (fd, 'w')
            f.write ("%s\n" % os.getpid())
            f.close ()
        except OSError, e:
            if e.errno != errno.EEXIST :
                self.log_exception ()
                raise
            self.need_unlock = False
            self.log.error ('Lockfile exists: %s' % self.lockfile)
            sys.exit (1)
    # end def __init__

    def unlock (self) :
        if self.need_unlock :
            os.unlink (self.lockfile)
        self.need_unlock = False # prevent second attempt at removal
    # end def unlock

    __del__ = unlock
# end class Lock_Mixin

def exitstatus (cmd, status) :
    if not status :
        return ''
    sig = ''
    if os.WIFSIGNALED (status) :
        sig = " (caught signal %d)" % os.WTERMSIG (status)
    s = os.WEXITSTATUS (status)
    if not s : s = ''
    return 'WARNING: %s returned nonzero exit status %s%s' % (cmd, s, sig)
# end def exitstatus

class Process (_Named) :
    """ A process in a (multi-)pipe
    """

    by_pid = {}

    def __init__ \
        (self
        , name         = None
        , stdin        = None
        , stdout       = None
        , stderr       = None
        , bufsize      = 4096
        , close_stdin  = False
        , close_stdout = False
        , close_stderr = False
        , **kw
        ) :
        self.__super.__init__ (**kw)
        self.stdin        = stdin
        self.stdout       = stdout
        self.stderr       = stderr
        self.close_stdin  = close_stdin
        self.close_stdout = close_stdout
        self.close_stderr = close_stderr
        self.bufsize      = bufsize
        self.status       = None
        self.name         = name
        if not self.name :
            self.name     = self.clsname
        self.children     = []
        self.tee          = None
        self.pid          = None
        self.toclose      = []
    # end def __init__

    def fork (self) :
        pid = os.fork ()
        if pid : # parent
            self.pid = pid
            #print "PID:", self.name, self.pid
            self.by_pid [pid] = self
            if self.stdout and self.close_stdout :
                #print "main closing:", self.stdout.fileno ()
                self.stdout.close ()
            if self.stderr and self.close_stderr :
                self.stderr.close ()
            if self.stdin and self.close_stdin :
                #print "main closing:", self.stdin.fileno ()
                self.stdin.close ()
            if hasattr (self, 'stdouts') :
                for f in self.stdouts.iterkeys () :
                    #print "main closing:", f.fileno ()
                    f.close ()
        else : # child
            for f in self.toclose :
                #print self.name, "closing:", f.fileno ()
                f.close ()
            self.method ()
            sys.exit    (0)
        return pid
    # end def fork

    def method (self) :
        raise NotImplementedError
    # end def method

    def run (self) :
        return self.fork ()
    # end def run

    @classmethod
    def wait (cls) :
        while cls.by_pid :
            #print cls.by_pid.keys ()
            pid, status = os.wait ()
            if pid > 0 :
                cls.by_pid [pid].status = status
            del cls.by_pid [pid]
    # end def wait

    def __repr__ (self) :
        r = []
        r.append ('%s:' % self.name)
        if self.stdin :
            r.append ('  stdin set')
        if self.stdout :
            r.append ('  stdout set')
        if self.stderr :
            r.append ('  stderr set')
        if self.bufsize :
            r.append ('  bufsize = %s' % self.bufsize)
        return '\n'.join (r)
    # end def __repr__
    __str__ = __repr__

# end class Process

class Tee (Process) :
    """ A tee in a pipe (like the unix command tee but copies to several
        sub-processes)
    """
    def __init__ (self, children, stdout, **kw) :
        self.stdouts  = {}
        self.__super.__init__ (**kw)
        self.children = children
        for c in self.children :
            pipe = os.pipe ()
            #print "tee pipe:", pipe
            self.stdouts [os.fdopen (pipe [1], 'w')] = c
            c.stdin = os.fdopen (pipe [0], 'r')
        self.toclose.append (stdout)
        for c in self.children :
            c.toclose.extend (self.stdouts.keys ())
            c.toclose.append (stdout)
            if self.stdin :
                c.toclose.append (self.stdin)
            for c2 in reversed (self.children) :
                if c == c2 :
                    break;
                c.toclose.append (c2.stdin)
    # end def __init__

    def method (self) :
        #print self.name, "method"
        while 1 :
            #print self.name, "before read", self.stdin.fileno ()
            buf = self.stdin.read (self.bufsize)
            #print "read:", len (buf)
            if not buf :
                #print "Tee: empty read, terminating"
                return
            # use items () here, we want to modify dict
            written = False
            for stdout, child in self.stdouts.items () :
                if not child :
                    continue
                try :
                    stdout.write (buf)
                    written = True
                    #print "written:", child.name, len (buf)
                except IOError, cause :
                    # this client died, no longer try to send to it
                    if cause.errno != errno.EPIPE :
                        raise
                    #print "Dead:", child.name
                    self.stdouts [stdout] = False
            # still clients existing?
            if not written :
                return
    # end def method

# end class Tee

class Method_Process (Process) :
    """ A process in a (multi-)pipe which runs a given method
    """
    def __init__ (self, name = None, **kw) :
        if 'method' in kw :
            self._method = kw ['method']
        self.name      = name
        if not self.name :
            self.name  = self._method.__name__
        self.__super.__init__ (name = self.name, **kw)
    # end def __init__

    def append (self, child) :
        assert (not self.stdout)
        assert (not child.stdin)
        self.children.append (child)
    # end def append

    def method (self) :
        self.redirect ()
        self._method ()
    # end def method

    def redirect (self) :
        if self.stdin :
            os.dup2 (self.stdin.fileno (), sys.stdin.fileno ())
        if self.stdout :
            os.dup2 (self.stdout.fileno (), sys.stdout.fileno ())
        if self.stderr :
            os.dup2 (self.stderr.fileno (), sys.stderr.fileno ())
        if self.stdin :
            self.stdin.close ()
        if self.stdout :
            self.stdout.close ()
        if self.stderr :
            self.stderr.close ()
    # end def redirect

    def run (self) :
        if self.children :
            pipe  = os.pipe ()
            #print "pipe:", pipe
            stdin = os.fdopen (pipe [0], 'r')
            self.stdout = os.fdopen (pipe [1], 'w')
            if len (self.children) > 1 :
                self.tee = Tee \
                    ( self.children
                    , stdin        = stdin
                    , stdout       = self.stdout
                    , bufsize      = self.bufsize
                    , close_stdin  = True
                    , close_stdout = True
                    )
            elif len (self.children) :
                child = self.children [0]
                child.stdin = stdin
                child.toclose.append (self.stdout)
        for child in self.children :
            child.run ()
        if self.tee :
            pid = self.tee.run ()
            self.by_pid [pid] = self.tee
        return self.fork ()
    # end def run

# end class Method_Process

class Exec_Process (Method_Process) :
    """ Process that execs a subcommand """
    def __init__ (self, cmd, args = None, name = None, **kw) :
        self.cmd  = cmd
        self.args = args
        if not args :
            self.args = [cmd]
        if not name :
            name = self.cmd
        self.__super.__init__ (name = name, **kw)
    # end def __init__

    def method (self) :
        self.redirect ()
        os.execv (self.cmd, self.args)
    # end def method

    def __repr__ (self) :
        r = [self.__super.__repr__ ()]
        r.append ('  cmd = %s' % self.cmd)
        r.append ('  args =')
        for a in self.args :
            r.append ('    %s' % a)
        return '\n'.join (r)
    # end def __repr__

# end class Exec_Process

def run_process (cmd, ** kw) :
    """ Convenience function that sets up a single Exec_Process, calls
        it, and returns a suitable error message if any.
    """
    cmd = Exec_Process (cmd, ** kw)
    cmd.run  ()
    cmd.wait ()
    return exitstatus (cmd.name, cmd.status)
# end def run_process
