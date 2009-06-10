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
from   logging.handlers import SysLogHandler
from   traceback        import format_exc
from   subprocess       import Popen, PIPE
from   rsclib.autosuper import autosuper

class Exec_Error    (RuntimeError) : pass

class _Named (autosuper) :
    def _name (self) :
        return self.__class__.__name__.lower ().replace ('_', '-')
    # end def _name

    clsname = property (_name)
# end class _Named

class Log (_Named) :
    """ Logger mixin. Sets up a log prefix automagically but can take
        arguments for setting log_level and log_prefix.
        Use as self.log.debug (msg), self.log.info (msg) etc.
    """
    def __init__ (self, log_level = None, log_prefix = None, *args, **kw) :
        log_prefix = log_prefix or 'ast-%s' % self.clsname
        self.log   = logging.getLogger (log_prefix)
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
        (self, args, stdin = None, ignore_err = False, shell = False) :
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
        if p.returncode != 0 :
            arg = args [0]
            if shell :
                arg = args
            msg = "Nonzero exitcode %s from %s" % (p.returncode, arg)
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
        self.is_locked = False
        self.__super.__init__ (*args, **kw)
        self.lockfile = '/var/lock/%s.lock' % self.clsname
        try :
            fd = os.open (self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close (fd)
        except OSError, e:
            if e.errno != errno.EEXIST :
                self.log_exception ()
                raise
            self.is_locked = True
            self.log.error ('Lockfile exists: %s' % self.lockfile)
            sys.exit (1)
    # end def __init__

    def __del__ (self) :
        if not self.is_locked :
            os.unlink (self.lockfile)
    # end def __del__
# end class Lock_Mixin
