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

import signal
from   rsclib.autosuper import autosuper

class Timeout_Error (RuntimeError) : pass

class Timeout (autosuper) :
    """ A class to model a timeout. Put a arm_alarm / disable_alarm
        around an action that needs a timeout. If everything works ok,
        nothing happens. If the timeout triggers a Timeout_Error is
        raised.
        This uses SIGALRM, so this may not be used anywhere else. Also
        nested timeouts are currently not possible.
    """
    def arm_alarm (self, timeout = 10) :
        self.osig = signal.signal (signal.SIGALRM, self.sig_alarm)
        signal.alarm  (timeout)
    # end def arm_alarm

    def disable_alarm (self) :
        signal.alarm  (0)
        signal.signal (signal.SIGALRM, self.osig)
    # end def disable_alarm

    def sig_alarm (self, sig, frame) :
        if hasattr (self, 'log') :
            self.log.debug ("SIGALRM received")
        raise Timeout_Error ("SIGALRM")
    # end def sig_alarm
# end class Timeout
