#!/usr/bin/python

import csv
import time
from   gzip             import open as gzopen
from   rsclib.autosuper import autosuper

class CDR (autosuper) :
    def __init__ (self, dictionary) :
        self.dict = dictionary
        self.dict ['uniqueid'] = self.dict ['uniqueid'].rstrip ()
    # end def __init__

    def __getattr__ (self, name) :
        if name in self.dict :
            value = self.dict [name]
            setattr (self, name, self.dict [name])
            return value
        raise AttributeError, name
    # end def __getattr__

    def __getitem__ (self, name) :
        return self.dict [name]
    # end def __getitem__
# end class CDR

class CDR_Parser (autosuper) :
    """ Parse Asterisk CDR records, see CDR_Parser.fields for an
        explanation of asterisk CDR fields.

        >>> from StringIO import StringIO
        >>> line = ('"","3","11","attendo","3","lcr/439","IAX2/pbx-14597",'
        ...         '"Read","dtmf||20|noanswer||3","2009-04-23 15:16:52",'
        ...         '"2009-04-23 15:16:52","2009-04-23 15:17:37",45,45,'
        ...         '"ANSWERED","DOCUMENTATION","asterisk-1240499812.774",'
        ...         '"102441/54"'
        ...        )
        >>> p = CDR_Parser (StringIO (line))
        >>> for cdr in p.iter () :
        ...     print cdr.amaflags, cdr.disposition, cdr ['channel'], cdr.dst
        DOCUMENTATION ANSWERED lcr/439 11
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
        , ('userfield'  , "A user-defined field, maximum 255 characters")
        , ('uniqueid'   , "Unique Channel Identifier")
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
