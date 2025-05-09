#!/usr/bin/python3
# Copyright (C) 2009-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__ import print_function
import csv
import time
from   gzip             import open as gzopen
from   datetime         import datetime
from   rsclib.autosuper import autosuper

class CDR (autosuper) :

    ama_table = \
        { 'OMIT'          : 1
        , 'BILLING'       : 2
        , 'DOCUMENTATION' : 3
        }

    non_db_fields = dict.fromkeys (('start', 'answer', 'end'))

    def __init__ (self, dictionary) :
        self.dict = dictionary
    # end def __init__

    def __getattr__ (self, name) :
        if name.startswith ('db_') and name [3:] in self.dict :
            value = self.dict [name [3:]]
        elif name in self.dict :
            value = self.dict [name]
        else :
            raise AttributeError (name)
        setattr (self, name, value)
        return value
    # end def __getattr__

    def __getitem__ (self, name) :
        try :
            return getattr (self, name)
        except AttributeError :
            raise KeyError (name)
    # end def __getitem__

    def __repr__ (self) :
        return repr (self.dict)
    # end def __repr__
    __str__ = __repr__

    @property
    def db_dict (self) :
        return dict ((i, self ['db_' + i]) for i in self.db_fields ())
    # end def db_dict

    @classmethod
    def db_fields (cls) :
        for f, dummy in CDR_Parser.fields :
            if f in cls.non_db_fields :
                continue
            yield f
        yield 'calldate'
    # end def db_fields

    def db_props (self) :
        return (self ['db_' + i] for i in self.db_fields ())
    # end def db_props

    @property
    def calldate (self) :
        return datetime.strptime (self.start, "%Y-%m-%d %H:%M:%S")
    # end def calldate
    db_calldate = calldate

    @property
    def db_amaflags (self) :
        return self.ama_table [self.amaflags]
    # end def db_amaflags
# end class CDR

class CDR_Parser (autosuper) :
    """ Parse Asterisk CDR records, see CDR_Parser.fields for an
        explanation of asterisk CDR fields.

        >>> from rsclib.pycompat import StringIO
        >>> line = ('"","3","11","attendo","3","lcr/439","IAX2/pbx-14597",'
        ...         '"Read","dtmf||20|noanswer||3","2009-04-23 15:16:52",'
        ...         '"2009-04-23 15:16:52","2009-04-23 15:17:37",45,45,'
        ...         '"ANSWERED","DOCUMENTATION","asterisk-1240499812.774",'
        ...         '"102441/54"'
        ...        )
        >>> line = line + '\\n' + line + '\\n'
        >>> p = CDR_Parser (StringIO (line))
        >>> for cdr in p.iter () :
        ...     print (cdr.amaflags, cdr.disposition, cdr ['channel'], cdr.dst)
        ...     print (cdr.uniqueid, cdr.userfield)
        ...     print ("TEST")
        DOCUMENTATION ANSWERED lcr/439 11
        asterisk-1240499812.774 102441/54
        TEST
        DOCUMENTATION ANSWERED lcr/439 11
        asterisk-1240499812.774 102441/54
        TEST
        >>> p = CDR_Parser (StringIO (line))
        >>> for cdr in p.iter () :
        ...     print (cdr.db_dst)
        ...     print (list (cdr.db_fields ()) [-1])
        ...     print (list (cdr.db_props  ()) [-1])
        ...     print (cdr.db_dict ['amaflags'])
        11
        calldate
        2009-04-23 15:16:52
        3
        11
        calldate
        2009-04-23 15:16:52
        3
    """
    fields = \
        ( ('accountcode', "What account number to use")
        , ('src'        , "Caller*ID number")
        , ('dst'        , "Destination extension")
        , ('dcontext'   , "Destination context")
        , ('clid'       , "Caller*ID with text")
        , ('channel'    , "Channel used")
        , ('dstchannel' , "Destination channel if appropriate")
        , ('lastapp'    , "Last application if appropriate")
        , ('lastdata'   , "Last application data (arguments)")
        , ('start'      , "Start of call (date/time)")
        , ('answer'     , "Anwer of call (date/time)")
        , ('end'        , "End of call (date/time)")
        , ('duration'   , "Total time in system, in seconds (integer), "
                          "from dial to hangup")
        , ('billsec'    , "Total time call is up, in seconds (integer), "
                          "from answer to hangup")
        , ('disposition', "What happened to the call: "
                          "ANSWERED, NO ANSWER, BUSY, FAILED")
        , ('amaflags'   , "DOCUMENTATION, BILLING, IGNORE etc, "
                          "specified on a per channel ")
        , ('uniqueid'   , "Unique Channel Identifier")
        , ('userfield'  , "A user-defined field, maximum 255 characters")
        )

    def __init__ (self, * files) :
        self.files = files
    # end def __init__

    def iter (self) :
        """ Iterator works only once if self.files are file objects """
        for f in self.files :
            if hasattr (f, 'read') :
                fd = f
            else :
                if f.endswith ('.gz') :
                    fd = gzopen (f, 'r')
                else :
                    fd = open   (f, 'r')
            reader = csv.DictReader \
                ( fd
                , fieldnames = [fld [0] for fld in self.fields]
                , dialect    = 'excel'
                , delimiter  = ','
                )
            for record in reader :
                yield (CDR (record))
            fd.close ()
    # end def iter

# end class CDR_Parser

if __name__ == '__main__' :
    pass
