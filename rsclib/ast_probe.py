#!/usr/bin/python
# Copyright (C) 2015-23 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__         import print_function
import sys
from time               import sleep
from asterisk.manager   import Manager, ManagerSocketException
from rsclib.execute     import Log
from rsclib.Config_File import Config_File

class Config (Config_File):

    def __init__ (self, config = 'ast_probe', path = '/etc/ast_probe'):
        self.__super.__init__ \
            ( path, config
            , ASTERISK_HOST         = 'localhost'
            , ASTERISK_MGR_ACCOUNT  = 'user'
            , ASTERISK_MGR_PASSWORD = 'secret'
            )
    # end def __init__

# end class Config

class Asterisk_Probe (Log):

    def __init__ \
        ( self
        , config  = 'ast_probe'
        , cfgpath = '/etc/ast_probe'
        , cfg     = None
        , retries = 0
        , ** kw
        ):
        if cfg:
            self.cfg = cfg
        else:
            self.cfg = cfg = Config (config = config, path = cfgpath)
        self.__super.__init__ (** kw)
        if 'manager' in kw:
            self.mgr = mgr = kw ['manager']
        else:
            self.mgr = mgr = Manager ()
            for r in range (retries + 1):
                try:
                    mgr.connect (cfg.ASTERISK_HOST)
                    break
                except ManagerSocketException:
                    if r >= retries:
                        raise
                    sleep (1)
            mgr.login (cfg.ASTERISK_MGR_ACCOUNT, cfg.ASTERISK_MGR_PASSWORD)
    # end def __init__

    def close (self):
        self.mgr.close ()
        self.mgr = None
    # end def close

    def probe_apps (self):
        mgr = self.mgr
        r = mgr.command ('core show applications')
        d = {}
        for line in r.data.split ('\n'):
            line = line.strip ()
            try:
                k, v = (x.strip () for x in line.split (':', 1))
            except ValueError:
                assert (  not line
                       or line == '--END COMMAND--'
                       or line.startswith ('-=') and line.endswith ('=-')
                       )
                continue
            d [k] = v
        return d
    # end def probe_apps

    def probe_sip_registry (self):
        r = self.mgr.command ('sip show registry')
        d = {}
        for line in r.data.split ('\n'):
            data = line.split (None, 5)
            if len (data) != 6:
                assert data == [] or data [1] == 'SIP' or data [0] == '--END'
                continue
            if data [0] == 'Host':
                continue
            if data [4] == 'Request' and data [5].startswith ('Sent'):
                data [4] = 'Request Sent'
                data [5] = data [5].split (None, 1) [-1]
            host, port = data [0].split (':', 1)
            d [host] = data [4]
        return d
    # end def probe_sip_registry

    def reload_sip (self):
        r = self.mgr.command ('sip reload')
        self.log.info ('SIP reload')
    # end def reload_sip

# end class Asterisk_Probe

def sip_check ():
    p = Asterisk_Probe ()
    r = p.probe_sip_registry ()
    reload = False
    for name in sys.argv [1:]:
        if name not in r:
            p.log.error ("Host %s not found" % name)
        elif r [name] == 'Request Sent':
            p.log.warn ("Host %s: %s" % (name, r [name]))
        elif r [name] != 'Registered':
            p.log.error ("Host %s not registered: %s" % (name, r [name]))
            reload = True
        else:
            p.log.debug ("Host %s OK" % name)

    if reload:
        p.reload_sip ()
# end def sip_check

if __name__ == '__main__':
    ap = Asterisk_Probe ()
    d = ap.probe_apps ()
    for k in d:
        v = d [k]
        print ("%s: %s" % (k, v))
    ap.close ()
