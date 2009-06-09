#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# ****************************************************************************

import os
import sys
import signal
import time
import logging
import errno
from   logging.handlers import SysLogHandler
from   traceback        import format_exc
from   socket           import socket, AF_INET, SOCK_STREAM
from   socket           import error as socket_error
from subprocess         import Popen, PIPE
from   rsclib.autosuper import autosuper

class Timeout_Error (RuntimeError) : pass
class Exec_Error    (RuntimeError) : pass
class Connect_Error (RuntimeError) : pass

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
        log_level  = log_level or logging.DEBUG
        log_prefix = log_prefix or 'ast-%s' % self.clsname
        formatter  = logging.Formatter \
            ('%s[%%(process)d]: %%(message)s' % log_prefix)
        handler    = SysLogHandler ('/dev/log', 'daemon')
        handler.setLevel     (log_level)
        handler.setFormatter (formatter)
        self.log   = logging.getLogger (log_prefix)
        self.log.addHandler (handler)
        self.log.setLevel (log_level)
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

class Server (Log) :
    """ Minimal server class for reading variables from stdin.
        Needs a logger instance in self.log
    """
    def __init__ (self, *args, **kw) :
        self.__super.__init__ (*args, **kw)
        self.error = None
    # end def __init__

    def read (self) :
        self.variables = {}
        logmsg = []
        line = sys.stdin.readline ()
        while line and line.strip () :
            if ':' not in line :
                self.nak  ("Invalid line received: %s" % line.rstrip ())
                self.exit ()
            self.variables.update ([(x.strip () for x in line.split (':', 1))])
            logmsg.append (line.rstrip ())
            line = sys.stdin.readline ()
        self.log.info ('Got: %s' % ', '.join (logmsg))
    # end def read

    def nak (self, msg = None) :
        self.log.error ("Sending NAK %s" % (msg or ''))
        if msg :
            print "%s\r" % msg
        print "NAK\r\n\r"
        sys.stdout.flush ()
        self.error = True
    # end def nak

    def ok (self) :
        self.log.info ("Sending OK")
        if not self.error :
            print "OK\r\n\r"
        sys.stdout.flush ()
        self.error = False
    # end def ok

    def exit (self) :
        if self.error is None :
            self.ok ()
        sys.exit (self.error)
    # end def exit

    def log_exception (self) :
        self.__super.log_exception   ()
        self.__super.print_exception ()
        self.nak                     ()
    # end def log_exception
# end class Server

class Client (Log) :
    """ Minimal server class for reading variables from stdin.
        Needs a logger instance in self.log
    """
    def __init__ (self, *args, **kw) :
        self.__super.__init__ (*args, **kw)
        self.written = []
        self.flushed = False
    # end def __init__

    def close (self) :
        self.flush      ()
        self.file.close ()
    # end def close

    def flush (self) :
        if not self.flushed :
            self.flushed = True
            print >> self.file, "\r\n\r"
            self.file.flush ()
            self.log.info ("Sent: %s" % ', '.join (self.written))
            self.written = []
    # end def flush

    def open (self, host, port) :
        self.log.info ("open: %s/%s" % (host, port))
        s = socket (AF_INET, SOCK_STREAM)
        s.connect  ((host, port))
        self.local_ip, self.local_port = s.getsockname ()
        self.file = s.makefile ('rw')
        s.close        ()
        self.flushed = False
        return self.file
    # end def open

    @property
    def ip (self) :
        return '%03d%03d%03d%03d' % tuple \
            (int (i) for i in self.local_ip.split ('.'))
    # end def ip

    def open_list \
	( self
        , host_port_list
        , timeout = 10
        , handler = None
        , retries = -1
        ) :
        """ Try opening a list of destination (host, port).
            Whenever we get an error we try the next host/port in the list.
            We set a timeout (using signal.alarm) before trying to
            connect. If the alarm comes before we can connect, the
            connect will get interrupted and we get an exception. Thus
            we can limit the time we try each host, even if the packets
            to this host are lost completely (e.g. because the port is
            firewalled as opposed to a closed port where we get back an
            icmp port unreachable).
            We try the list repeatedly until we can connect or we are
            terminated by asterisk because the call terminated. By
            default (retries parameter negative) we try indefinitely,
            but the number of retries can be limited.
            We wait 5 seconds before re-trying the list, otherwise we
            may fill log-files if the CRM isn't available.
            If handler is callable, we execute the handler while the
            alarm is still active and try the next host if the handler
            didn't complete in time.
        """
        osig = signal.signal (signal.SIGALRM, self.sig_alarm)
        retr = retries
        while True :
            for host, port in host_port_list :
                try :
                    signal.alarm  (timeout)
                    self.open     (host, port)
                    if callable (handler) :
                        handler ()
                    signal.alarm  (0)
                    signal.signal (signal.SIGALRM, osig)
                    return
                except socket_error, cause :
                    self.log.error \
                        ("Failed connection to %s/%s: %s" % (host, port, cause))
                except Timeout_Error :
                    self.log.error \
                        ("Timeout while connecting to %s/%s" % (host, port))
            if retr :
                time.sleep (5)
                if retr > 0 :
                    retr -= 1
            else :
                raise Connect_Error, \
                    "No CRM host reachable after %s retries" % retries
    # end def open_list

    def sig_alarm (self, sig, frame) :
        self.log.debug ("SIGALRM received")
        raise Timeout_Error, "SIGALRM"
    # end def sig_alarm

    def parse_answer (self) :
        """ Parse answer from remote server. We allow either several
            lines before a 'NAK' or 'OK' or a single NAK-line with the
            message trailing after a colon for backward compatitibility.
        """
        self.result = 'unknown'
        result = [self.file.readline ().strip ()]
        while (   result [-1]
              and result [-1] != 'OK'
              and not result [-1].startswith ('NAK')
              ) :
            self.log.debug (result [-1])
            result.append (self.file.readline ().strip ())
        self.message = result [:-1]
        self.result  = result [-1]
        if not self.result :
            self.result = 'unknown'
        # Backward compatibility
        if self.result.startswith ('NAK:') :
            self.message.append (result.split (':', 1) [1])
            self.result = 'NAK'
    # end def parse_answer

    def write (self, string) :
        print >> self.file, "%s\r" % string
        self.written.append (string)
    # end def write

# end class Client

class Exec (Log) :
    def error (self, msg) :
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
            msg = "Nonzero exitcode from %s" % arg
            self.error (msg)
            for e in stderr.rstrip ().split ('\n') :
                self.error (e)
            if not ignore_err :
                raise Exec_Error, msg
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
