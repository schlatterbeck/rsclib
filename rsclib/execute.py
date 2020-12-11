#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__ import print_function
import os
import sys
import logging
import errno
import signal
import atexit
from   copy             import copy
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
            if 'log_handler' in args :
                handler = args ['log_handler']
            else :
                handler = SysLogHandler ('/dev/log', 'daemon')
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
                print ("%s\r" % l)
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
        ( self, args
        , stdin      = None
	, ignore_err = False
	, shell      = False
	, charset    = 'utf-8'
	) :
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
        stdout, stderr = (x.decode (charset) for x in p.communicate (stdin))
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
                raise Exec_Error (msg, p.returncode)
        return stdout.rstrip ().split ('\n')
    # end def exec_pipe
# end class Exec

class Lock_Mixin (_Named) :
    def __init__ (self, do_lock = True, *args, **kw) :
        self.need_unlock = False
        self.__super.__init__ (*args, **kw)
        lockdir = os.environ.get ('LOCKDIR', '/var/lock')
        if getattr (self, 'lockfile', None) :
            lf = self.lockfile
            if not lf.startswith ('/') :
                lf = os.path.join (lockdir, lf)
            if not lf.endswith ('.lock') :
                lf += '.lock'
            self.lockfile = lf
        else :
            self.lockfile = os.path.join (lockdir, '%s.lock' % self.clsname)
        if do_lock :
            self.lock ()
    # end def __init__

    def lock (self) :
        atexit.register (self.unlock)
        self.need_unlock = True
        try :
            fd = os.open (self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            f  = os.fdopen (fd, 'w')
            f.write ("%s\n" % os.getpid())
            f.close ()
        except OSError as e:
            if e.errno != errno.EEXIST :
                self.log_exception ()
                raise
            self.need_unlock = False
            self.log.error ('Lockfile exists: %s' % self.lockfile)
            self.lock_fail ()
    # end def lock

    def lock_fail (self) :
        """ By default we exit when locking fails. A derived class may
            want to override this.
        """
        sys.exit (1)
    # end def lock_fail

    def unlock (self) :
        if self.need_unlock :
            os.unlink (self.lockfile)
        self.need_unlock = False # prevent second attempt at removal
    # end def unlock
    __del__  = unlock

    def __exit__ (self, tp, value, tb) :
        if tb :
            self.log_exception ()
        # We do *not* return True, we didn't handle the exception
    # end def __exit__

    def __enter__ (self) :
        assert not self.need_unlock
        self.lock ()
    # end def __enter__

# end class Lock_Mixin

class Lock (Log, Lock_Mixin) :

    def __init__ (self, lockfile = None, ** kw) :
        self.lockfile = lockfile
        prefix = None
        if lockfile :
            prefix = lockfile.replace ('/', '-')
        self.__super.__init__ (do_lock = False, log_prefix = prefix, ** kw)
    # end def __init__

# end class Lock

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

class Process (Log) :
    """ A process in a (multi-)pipe
        Note that the file descriptors can take several different
        values:
        - None means: close this file descriptor if the respective
          close-flag (e.g. close_stdin) is also set. Leave
          file-descriptor alone if close flag is not set.
        - 'PIPE' means we want an pipe to (stdin) / from (stdout or
          stderr) this file descriptor
        - A non-zero value must be a normal file object where the fileno()
          can be extracted and used in dup2
    """

    by_pid      = {}

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
        self.stdin         = stdin
        self.stdout        = stdout
        self.stdouts       = {}
        self.stderr        = stderr
        self.close_stdin   = close_stdin
        self.close_stdout  = close_stdout
        self.close_stderr  = close_stderr
        self.bufsize       = bufsize
        self.status        = None
        self.name          = name
        self.log_prefix    = name # use default from Log class if unset
        self.children      = []
        self.stderr_child  = None
        self.tee           = None
        self.pid           = None
        self.stdin_w       = None
        self.stdout_r      = None
        self.stderr_r      = None
        # 'toclose' may contain files to close for all clients.
        # Will pick up all PIPE ends of all stdout and stderr and close
        # the read ends in all children. The write ends will be closed
        # after forking off the child with the PIPE end.
        self.toclose       = []
        self.sibling_files = []
        if not self.name :
            self.name = self.clsname
        self.__super.__init__ (log_prefix = self.log_prefix, **kw)
    # end def __init__

    def fork (self) :
        rclose = []
        if self.stdin == 'PIPE' :
            pipe = os.pipe ()
            self.stdin    = os.fdopen (pipe [0], 'r')
            self.stdin_w  = os.fdopen (pipe [1], 'w')
            self.toclose.append (self.stdin_w)
            self.close_stdin = True
        if self.stdout == 'PIPE' :
            pipe = os.pipe ()
            self.stdout   = os.fdopen (pipe [1], 'w')
            # to close after fork:
            self.stdouts [self.stdout] = 0
            self.stdout_r = os.fdopen (pipe [0], 'r')
            rclose.append (self.stdout_r)
            self.close_stdout = True
        elif self.close_stdout and self.stdout :
            self.stdouts [self.stdout] = 0
        if self.stderr == 'PIPE' :
            pipe = os.pipe ()
            self.stderr   = os.fdopen (pipe [1], 'w')
            self.stderr_r = os.fdopen (pipe [0], 'r')
            rclose.append (self.stderr_r)
            self.close_stderr = True
        pid = os.fork ()
        if pid : # parent
            self.pid = pid
            self.log.debug ("fork: pid: %s" % self.pid)
            self.by_pid [pid] = self
            if self.stderr and self.close_stderr :
                self.log.debug \
                    ("fork: closing stderr: %s" % self.stderr.fileno ())
                self.stderr.close ()
            if self.stdin and self.close_stdin :
                self.log.debug \
                    ("fork: closing stdin: %s" % self.stdin.fileno ())
                self.stdin.close ()
            if hasattr (self, 'stdouts') :
                for f in self.stdouts :
                    self.log.debug ("fork: aux closing: %s" % f.fileno ())
                    f.close ()
        else : # child
            for f in self.sibling_files :
                self.log.debug ("fork: child closing sibling: %s" % f.fileno ())
                f.close ()
            for f in self.toclose :
                self.log.debug ("fork: child closing toclose: %s" % f.fileno ())
                f.close ()
            # close children read descriptors in parent
            for c in self.children :
                self.log.debug \
                    ( "closing stdin of %s->%s: %s"
                    % (self.name, c.name, c.stdin.fileno ())
                    )
                c.stdin.close ()
            # Python seems to ignore SIGPIPE by default, re-enable it
            signal.signal (signal.SIGPIPE, signal.SIG_DFL)

            self.redirect ()
            self.method   ()
            sys.exit      (0)
        return rclose
    # end def fork

    def method (self) :
        raise NotImplementedError
    # end def method

    def redirect (self) :
        self.log.debug ("In redirect")
        if self.stdin :
            self.log.debug \
                ( "stdin dup2: %s->%s"
                % (self.stdin.fileno (), sys.stdin.fileno ())
                )
            os.dup2 (self.stdin.fileno (), sys.stdin.fileno ())
        if self.stdout :
            self.log.debug \
                ( "stdout dup2: %s->%s"
                % (self.stdout.fileno (), sys.stdout.fileno ())
                )
            os.dup2 (self.stdout.fileno (), sys.stdout.fileno ())
        if self.stderr :
            self.log.debug \
                ( "stderr dup2: %s->%s"
                % (self.stderr.fileno (), sys.stderr.fileno ()))
            os.dup2 (self.stderr.fileno (), sys.stderr.fileno ())
        if self.stdin :
            self.stdin.close ()
        elif self.close_stdin :
            sys.stdin.close ()
        if self.stdout :
            self.stdout.close ()
        elif self.close_stdout :
            sys.stdout.close ()
        if self.stderr :
            self.stderr.close ()
        elif self.close_stderr :
            sys.stderr.close ()
    # end def redirect

    def run (self) :
        sibling_files = []
        for c in reversed (self.children) :
            pipe = os.pipe ()
            self.stdouts [os.fdopen (pipe [1], 'w')] = c
            c.stdin = os.fdopen (pipe [0], 'r')
            c.close_stdin = True
            self.log.debug \
                ( "Setting sibling-files: %s->%s to %s"
                % (self.name, c.name, [x.fileno () for x in sibling_files])
                )
            c.sibling_files = copy (sibling_files)
            c.sibling_files.extend (self.sibling_files)
            sibling_files.append (c.stdin)
        # For dup2 in redirect to do its job:
        if len (self.children) == 1 :
            self.stdout = self.stdouts.keys () [0]
        if self.stderr_child :
            pipe = os.pipe ()
            self.stderr = os.fdopen (pipe [1], 'w')
            self.close_stderr = True
            self.stderr_child.stdin = os.fdopen (pipe [0], 'r')
            self.stderr_child.close_stdin = True
            self.stderr_child.sibling_files = sibling_files
            self.stderr_child.sibling_files.extend (self.sibling_files)
            self.children.insert (0, self.stderr_child)
        toclose = self.fork ()
        for child in self.children :
            self.log.debug \
                ( "passing toclose to %s: %s"
                % (child.name, [x.fileno () for x in self.toclose + toclose])
                )
            child.toclose.extend (self.toclose + toclose)
            toclose.extend (child.run ())
        self.log.debug \
            ("toclose: %s" % ([x.fileno () for x in toclose]))
        return toclose
    # end def run

    @classmethod
    def wait (cls) :
        while cls.by_pid :
            pid, status = os.wait ()
            if pid > 0 :
                process = cls.by_pid [pid]
                if status :
                    process.log.info \
                        ( "pid: %s: %s"
                        % (pid, exitstatus (process.name, status))
                        )
                process.status = status
                del cls.by_pid [pid]
    # end def wait

    def _add_buffer_process (self, found = False) :
        if self.stderr == 'PIPE' :
            self.log.debug ("found stderr PIPE: %s", self.name)
            if found :
                self.stderr = None
                self.set_stderr_process (Buffer_Process (stderr = 'PIPE'))
            found = True
        if self.stdout == 'PIPE' :
            self.log.debug ("found stdout PIPE: %s", self.name)
            if found :
                self.stdout = None
                self.append (Buffer_Process (stdout = 'PIPE'))
            found = True
        else :
            for c in self.children :
                found = c._add_buffer_process (found)
        return found
    # end def _add_buffer_process

    def _read_outputs (self) :
        stdout = ''
        stderr = ''
        if self.stderr_r :
            self.log.debug ("reading stderr: %s", self.name)
            stderr = self.stderr_r.read ()
        if self.stdout_r :
            self.log.debug ("reading stdout: %s", self.name)
            stdout = self.stdout_r.read ()
        sout_l = [stdout]
        serr_l = [stderr]
        for c in self.children :
            sout, serr = c._read_outputs ()
            sout_l.append (sout)
            serr_l.append (serr)
        return ''.join (sout_l), ''.join (serr_l)
    # end def _read_outputs

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
    """ A tee in a pipe (like the unix command "tee" but copies to several
        sub-processes)
    """
    def __init__ (self, children, **kw) :
        self.stdouts  = {}
        self.__super.__init__ (**kw)
        self.children = children
    # end def __init__

    def method (self) :
        while 1 :
            buf = sys.stdin.read (self.bufsize)
            if not buf :
                self.log.debug ("Tee: empty read, terminating")
                return
            # use items () here, we want to modify dict
            written = False
            for stdout, child in self.stdouts.items () :
                if not child :
                    continue
                try :
                    stdout.write (buf)
                    written = True
                    #self.log.debug ("written: %s" % len (buf))
                except IOError as cause :
                    # this client died, no longer try to send to it
                    if cause.errno != errno.EPIPE :
                        raise
                    self.log.debug ("%s: dead" % child.name)
                    stdout.close ()
                    del self.stdouts [stdout]
            # still clients existing?
            if not written :
                if len (self.stdouts) :
                    self.log.err ("All children had sigpipe ?!?")
                return
    # end def method

# end class Tee

class Method_Process (Process) :
    """ A process in a (multi-)pipe which runs a given method
    """
    def __init__ (self, name = None, **kw) :
        self.tee = None
        if 'method' in kw :
            self.method = kw ['method']
        self.name      = name
        if not self.name :
            self.name  = self.method.__name__
        self.__super.__init__ (name = self.name, **kw)
    # end def __init__

    def append (self, child) :
        assert self.stdout is None
        assert child.stdin is None
        if self.children :
            assert len (self.children) == 1
            if not self.tee :
                self.tee = Tee \
                    (self.children, bufsize = self.bufsize)
                self.children = [self.tee]
            self.tee.children.append (child)
        else :
            self.children.append (child)
    # end def append

    def communicate (self, input = None) :
        assert input is None or self.stdin == 'PIPE'
        p = self
        if self.stdin == 'PIPE' :
            self.stdin = None
            if self.input is not None :
                p = Echo_Process (message = str (input))
                p.append (self)
        # Add a Buffer_Process for each PIPE output in tree order.
        # Only the very first is left unbuffered.
        self._add_buffer_process ()
        p.run ()
        # Now get outputs/errors in tree order
        stdout, stderr = self._read_outputs ()
        p.wait ()
        return stdout, stderr
    # end def communicate

    def set_stderr_process (self, child) :
        assert self.stderr is None
        assert self.stderr_child is None
        assert child.stdin is None
        self.stderr_child = child
    # end def set_stderr_process

# end class Method_Process

class Buffer_Process (Method_Process) :
    """ First read *everything* from stdin, then write this to stdout.
        So everything is buffered in-memory. Used to decouple reading
        from multiple streams.
    """

    def __init__ (self, ** kw) :
        self.__super.__init__ (method = self.copy, ** kw)
        if self.stdout == 'PIPE' :
            self.io = sys.stdout
        else :
            assert self.stderr == 'PIPE'
            self.io = sys.stderr
    # end def __init__

    def copy (self) :
        buf = sys.stdin.read ()
        self.log.debug ("read: %s" % len (buf))
        self.log.debug ("write: fd=%s" % self.io.fileno ())
        self.io.write (buf)
        self.io.flush ()
    # end def echo

# end class Buffer_Process

class Echo_Process (Method_Process) :
    """ Simply echo a message given in constructor to stdout.
        Useful for specifying a constant input to a pipeline.
    """

    def __init__ (self, message, ** kw) :
        self.message = message
        self.__super.__init__ \
            ( method       = self.echo
            , close_stdin  = True
            , ** kw
            )
    # end def __init__

    def echo (self) :
        sys.stdout.write (self.message)
    # end def echo

# end class Echo_Process

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
