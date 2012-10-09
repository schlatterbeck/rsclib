#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import sys
import re
import csv

from   datetime           import datetime, tzinfo, timedelta
from   rsclib.stateparser import Parser
from   rsclib.autosuper   import autosuper

class TZ (tzinfo) :
    def __init__ (self, offset = 0) :
        self.offset = int (offset, 10)
    # end def __init__

    def utcoffset (self, dt = None) :
        return timedelta (hours = self.offset)
    # end def utcoffset

    def __str__ (self) :
        return "TZ (%s)" % self.offset
    # end def __str__
    __repr__ = __str__

# end class TZ

sql_bool = {'t' : True, 'f' : False}

class SQL_boolean (autosuper) :
    """ Parse boolean from sql dump and return as python bool.
    >>> b = SQL_boolean ()
    >>> b ('\\N')
    >>> b ('NULL')
    >>> b ('f')
    False
    >>> b ('t')
    True
    """

    def __call__ (self, b) :
        if b == '\\N' or b == 'NULL' :
            return None
        return sql_bool [b]
    # end def __call__

# end class SQL_boolean

class SQL_double (autosuper) :

    def __call__ (self, f) :
        if f == '\\N' or f == 'NULL' :
            return None
        return float (f)
    # end def __call__

# end class SQL_double

class SQL_integer (autosuper) :

    def __call__ (self, i) :
        if i == '\\N' or i == 'NULL' :
            return None
        return int (i)
    # end def __call__

# end class SQL_integer
SQL_bigint = SQL_smallint = SQL_integer

class SQL_character (autosuper) :

    """ Get string from sql dump and convert to unicode.
    >>> sq = SQL_character ()
    >>> sq ('\xc3\x96ffnungswinkel')
    u'\\xd6ffnungswinkel'
    >>> sq.charset = 'latin1'
    >>> sq ('\xd6ffnungswinkel')
    u'\\xd6ffnungswinkel'
    """

    charset = 'utf-8'

    def __call__ (self, s) :
        if s == '\\N' or s == 'NULL' :
            return None
        return s.decode (self.charset)
    # end def __call__

# end class SQL_character
SQL_enum = SQL_text = SQL_varchar = SQL_character

class SQL_Timestamp_Without_Zone (autosuper) :
    """ convert sql timestamp with time zone.
    >>> ts = SQL_Timestamp_Without_Zone ()
    >>> ts ("0000-00-00 00:00:00")
    >>> ts ("2012-05-24 17:05:16.609")
    datetime.datetime(2012, 5, 24, 17, 5, 16, 609000)
    >>> ts ("2012-05-24 17:43:33")
    datetime.datetime(2012, 5, 24, 17, 43, 33)
    """

    def __call__ (self, ts) :
        if ts == '\\N' or ts == 'NULL' or ts == '0000-00-00 00:00:00' :
            return None
        format = '%Y-%m-%d %H:%M:%S.%f'
        if len (ts) == 19 :
            format = '%Y-%m-%d %H:%M:%S'
        return datetime.strptime (ts, format)
    # end def __call__

# end class SQL_Timestamp_Without_Zone

class SQL_Timestamp_With_Zone (SQL_Timestamp_Without_Zone) :
    """ convert sql timestamp with time zone.
    >>> ts = SQL_Timestamp_With_Zone ()
    >>> ts ("2011-01-17 20:12:09.04032+01")
    datetime.datetime(2011, 1, 17, 20, 12, 9, 40320, tzinfo=TZ (1))
    """
    def __call__ (self, ts) :
        if ts == '\\N' or ts == 'NULL' :
            return None
        d  = self.__super.__call__ (ts [:-3])
        tz = TZ (ts [-3:])
        return d.replace (tzinfo = tz)
    # end def __call__

# end class SQL_Timestamp_With_Zone

class SQL_date (autosuper) :
    """ convert sql date.
    >>> dt = SQL_date ()
    >>> dt ("2011-12-01")
    datetime.date(2011, 12, 1)
    """

    def __call__ (self, dt) :
        if dt == '\\N' or dt == 'NULL' or dt == '0000-00-00' :
            return None
        d  = datetime.strptime (dt, "%Y-%m-%d")
        return d.date ()
    # end def __call__

# end class SQL_date

def make_naive (dt) :
    """Make a naive datetime object."""
    if dt is None :
        return dt
    offs = dt.utcoffset ()
    if offs is None :
        return dt
    x = dt.replace (tzinfo = None)
    return x - offs
# end make_naive

class adict (dict) :

    def __init__ (self, *args, **kw) :
        self.done = False
        dict.__init__ (self, *args, **kw)
    # end def __init__

    def __getattr__ (self, key) :
        if key in self :
            return self [key]
        raise AttributeError, key
    # end def __getattr__

    def set_done (self, done = True) :
        self.done = done
    # end def set_done

# end class adict

class SQL_Parser (Parser) :

    re_charset = re.compile (r'CHARSET=([-a-zA-Z0-9]+)')
    re_copy    = re.compile (r'^COPY\s+(\S+)\s\(([^)]+)\) FROM stdin;$')
    re_endtbl  = re.compile (r'^\).*;$')
    re_func    = re.compile (r'^CREATE FUNCTION ([a-zA-Z0-9]+)\s*\(')
    re_insert  = re.compile \
        (r'INSERT INTO ["`]?([a-z0-9]+)["`]? VALUES \((.*)\);')
    re_table   = re.compile (r'^CREATE TABLE (\S+) \(')

    matrix = \
        [ ["init",  re_copy,   "copy",  "copy_start"]
        , ["init",  re_insert, "init",  "insert"]
        , ["init",  re_func,   "func",  None]
        , ["init",  re_table,  "table", "table_start"]
        , ["init",  None,      "init",  None]
        , ["copy",  '\\.',     "init",  None]
        , ["copy",  None,      "copy",  "copy_entry"]
        , ["func",  "END;",    "init",  None]
        , ["func",  "END;$$",  "init",  None]
        , ["func",  None,      "func",  None]
        , ["table", re_endtbl, "init",  "table_end"]
        , ["table", None,      "table", "table_entry"]
        ]

    def __init__ (self, *args, **kw) :
        self.contents = {}
        self.tables   = {}
        # remember column names in creation order, should really use an
        # OrderedDict in self.tables but this means at least python2.7
        self.columns  = {}
        self.__super.__init__ (*args, **kw)
    # end def __init__

    def copy_entry (self, state, new_state, match) :
        line       = self.line.rstrip ('\n')
        tbl        = self.table
        fields     = self.fields
        datafields = line.split ('\t')
        self.contents [self.tablename].append \
            (adict ((a, tbl [a] (b)) for a, b in zip (fields, datafields)))
    # end def copy_entry

    def copy_start (self, state, new_state, match) :
        self.tablename = match.group (1)
        self.table     = self.tables [self.tablename]
        self.fields    = [x.strip ('"') for x in match.group (2).split (', ')]
        self.contents [self.tablename] = []
    # end def copy_start

    def dump (self) :
        for tbl, ct in self.contents.iteritems () :
            print "Table: %s" % tbl
            for line in ct :
                print
                for k, v in line.iteritems () :
                    print "  %s: %s" % (k, repr (v))
    # end dump

    def insert (self, state, new_state, match) :
        """ This asumes the whole insert statement is one line. """
        name   = match.group (1)
        tuples = match.group (2).split ('),(')
        tbl    = self.tables  [name]
        fields = self.columns [name]
        self.contents [name] = []
        reader = csv.reader (tuples, delimiter = ',', quotechar="'")
        for t in reader :
            self.contents [name].append \
                (adict ((a, tbl [a] (b)) for a, b in zip (fields, t)))
    # end def insert

    def table_end (self, state, new_state, match) :
        """ End of table may contain charset specification in mysql.
            But the dump is in utf-8 anyway (!)
        """
        m = self.re_charset.search (self.line)
        if 0 :
            if m :
                for k in self.table.keys () :
                    setattr (self.table [k], 'charset', m.group (1))
        self.table = None
    # end def table_end

    def table_entry (self, state, new_state, match) :
        line = self.line.strip ()
        try :
            name, type, rest = line.split (None, 2)
        except ValueError :
            name, type = line.split (None, 1)
            if type.endswith (',') :
                type = type [:-1]
            rest = ''
        if name.startswith ('"') or name.startswith ('`') :
            name = name [1:-1]
        if type.startswith ('int(') or type.startswith ('tinyint(') :
            type = 'integer'
        if type.startswith ('varchar') :
            type = 'varchar'
        if type.startswith ('enum') :
            type = 'enum'
        if name in ('PRIMARY', 'UNIQUE') and type == 'KEY' :
            return
        if name == 'KEY' :
            return
        method = getattr (self, 'type_' + type, self.type_default)
        self.table [name] = method (type, rest)
        self.col.append (name)
    # end def table_entry

    def table_start (self, state, new_state, match) :
        name = match.group (1).strip ('`')
        self.table = self.tables  [name] = {}
        self.col   = self.columns [name] = []
    # end def table_start

    # Magic type methods for SQL types:

    def type_default (self, type, rest) :
        return globals () ['SQL_' + type] ()
    # end def type_default

    def type_character (self, type, rest) :
        assert (rest.startswith ('varying'))
        return self.type_default (type, rest)
    # end def type_character

    def type_double (self, type, rest) :
        assert (rest.startswith ('precision'))
        return self.type_default (type, rest)
    # end def type_double

    def type_timestamp (self, type, rest) :
        if rest.startswith ('with time zone') :
            return SQL_Timestamp_With_Zone ()
        elif rest.startswith ('without time zone') :
            return SQL_Timestamp_Without_Zone ()
        else :
            raise ValueError, "Invalid timestamp spec: %s" % rest
    # end def type_timestamp

    def type_datetime (self, type, rest) :
        return SQL_Timestamp_Without_Zone ()
    # end def type_datetime

    def type_varchar (self, type, rest) :
        return self.type_default (type, rest)
    # end def type_varchar


# end def SQL_Parser

if __name__ == "__main__" :
    if len (sys.argv) > 1 :
        f  = open (sys.argv [1])
    else :
        f = sys.stdin
    c = SQL_Parser ()
    c.parse (f)
    c.dump  ()
### __END__ sqlparser
