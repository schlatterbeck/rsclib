#!/usr/bin/python
# Copyright (C) 2009-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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
