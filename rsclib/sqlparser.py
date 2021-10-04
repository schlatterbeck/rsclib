#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2012-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from __future__ import unicode_literals

import sys
import re
import csv

from   datetime           import datetime, time, tzinfo, timedelta
from   rsclib.stateparser import Parser, Parse_Error
from   rsclib.autosuper   import autosuper
from   rsclib.pycompat    import ustr, string_types

class TZ (tzinfo) :
    def __init__ (self, offset = 0) :
        self.offset = int (offset, 10)
    # end def __init__

    def utcoffset (self, dt = None) :
        return timedelta (hours = self.offset)
    # end def utcoffset

    def dst (self, dt = None) :
        return timedelta (0)
    # end def dst

    def tzname (self, dt = None) :
        off = self.utcoffset ().seconds
        assert off % 3600 == 0
        off //= 3600
        sign = b'+'
        if off < 0 :
            sign = b'-'
        return b'%s%02d' % (sign, off)
    # end def tzname

    def __str__ (self) :
        return "TZ (%s)" % self.offset
    # end def __str__
    __repr__ = __str__

# end class TZ

sql_bool = {b't' : True, b'f' : False}

class SQL_Dialect_Postgres (autosuper) :
    """ SQL Dialect for Postgres """

    sql_null = b'\\N'

# end class SQL_Dialect_Postgres

class SQL_Dialect_Mysql (autosuper) :
    """ SQL Dialect for Postgres """

    sql_null = b'NULL'

# end class SQL_Dialect_Mysql

dialect_pg = SQL_Dialect_Postgres ()
dialect_my = SQL_Dialect_Mysql

class SQL_Type (autosuper) :

    def __init__ (self, *p) :
        self.parameters = p
    # end def __init__

    def format (self, dialect, typ, value) :
        if value is None :
            return dialect.sql_null
        # special case for date/time formats
        # We remove trailing 0s in the microsecond part and remove the
        # decimal dot if the microsecond part was all zero to make it
        # roundtrip
        if getattr (self, 'dtfmt', None) :
            return value.strftime (self.dtfmt).encode ('ascii')
        if getattr (self, 'timefmt', None) :
            v = value.strftime (self.timefmt).encode ('ascii')
            return v.rstrip (b'0').rstrip (b'.')
        return repr (value).encode ('ascii')
    # end def format

    def typ (self, tn) :
        if self.parameters :
            return b"%s(%s)" % (tn, b','.join (self.parameters))
        return tn
    # end def typ

# end class SQL_Type

class SQL_boolean (SQL_Type) :
    """ Parse boolean from sql dump and return as python bool.
    >>> b = SQL_boolean ()
    >>> b (b'\\N')
    >>> b (b'NULL')
    >>> b (b'f')
    False
    >>> b (b't')
    True
    """

    def __call__ (self, b) :
        if b == b'\\N' or b == b'NULL' :
            return None
        return sql_bool [b]
    # end def __call__

    def format (self, dialect, typ, value) :
        if value is None :
            return dialect.sql_null
        if value :
            return b't'
        return b'f'
    # end def format

# end class SQL_boolean

class SQL_double (SQL_Type) :

    def __call__ (self, f) :
        if f == b'\\N' or f == b'NULL' :
            return None
        return float (f)
    # end def __call__

# end class SQL_double

class SQL_real (SQL_Type) :

    def __call__ (self, f) :
        if f == b'\\N' or f == b'NULL' :
            return None
        return float (f)
    # end def __call__

# end class SQL_real

class SQL_integer (SQL_Type) :

    def __call__ (self, i) :
        if i == b'\\N' or i == b'NULL' :
            return None
        return int (i)
    # end def __call__

# end class SQL_integer
SQL_bigint = SQL_smallint = SQL_integer

class SQL_numeric (SQL_Type) :

    def __init__ (self, integer_part_len, fractional_part_len) :
        self.integer_part_len    = int (integer_part_len)
        self.fractional_part_len = int (fractional_part_len)
    # end def __init__

    def __call__ (self, n) :
        if n == b'\\N' or n == b'NULL' :
            return None
        a, b = n.split (b'.')
        return (int (a), int (b))
    # end def __call__

    def format (self, dialect, typ, value) :
        fmt = b"%%d.%%0%dd" % self.fractional_part_len
        if value is None :
            return dialect.sql_null
        return fmt % value
    # end def format

    def typ (self, tn) :
        il = self.integer_part_len
        fl = self.fractional_part_len
        return "%s(%s,%s)" % (tn, il, fl)
    # end def typ

# end class SQL_numeric

# For regression testing, doesn't work with doctest because doctest
# needs backslashes in strings escaped and accented characters are
# output as backslash-escapes in python2 and as rendered strings in
# python3 by default.
broken_strings_latin1 = \
    ( (b'\xd6ffnungswinkel', '\xd6ffnungswinkel')
    ,
    )
broken_strings_utf8 = \
    ( (b'\xc3\x96ffnungswinkel', '\xd6ffnungswinkel')
    ,
    )
broken_strings_utf8_double = \
    ( ( b'\xc3\x83\xc2\xa4\xc3\x83\xc2\xb6\xc3\x83\xc2\xbc\xc3\x83'
        b'\xc2\x84\xc3\x83\xc2\x96\xc3\x83\xc2\x9c\xc3\x83\xc2\x9f'
      , '\xe4\xf6\xfc\xc4\xd6\xdc\xdf'
      )
    , ( b'Conrad von H\xc3\x83\xc2\xb6tzendorf Stra\xc3\x83\xc5\xb8e'
      , 'Conrad von H\xf6tzendorf Stra\xdfe'
      )
    , ( b'Josefst\xc4\x82\xc2\xa4dter Stra\xc4\x82\xc5\xbae'
      , 'Josefst\xe4dter Stra\xdfe'
      )
    , ( b'Josefst\xc4\x82\xc2\xa4dter Stra\xc3\x83\xc2\x9fe'
      , 'Josefst\xe4dter Stra\xdfe'
      )
    , ( b'Sch\xc4\x82\xc2\xb6nburgstra\xc4\x82\xc5\xbae'
      , 'Sch\xf6nburgstra\xdfe'
      )
    , ( b'Wei\xc3\x83\xc2\x9fgerberl\xc4\x82\xc2\xa4nde'
      , 'Wei\xdfgerberl\xe4nde'
      )
    , ( b'M\xc4\x82\xc4\xbdller'
      , 'M\xfcller'
      )
    , ( b'\xc4\x82\xe2\x80\x93'
      , '\xd6'
      )
    , ( b'M\xc4\x8f\xc5\xbc\xcb\x9dller'
      , 'M\xfcller'
      )
    , ( b'M\xc4\x8f\xc5\xbc\xcb\x9dller'
      , 'M\xfcller'
      )
    , ( b'Thaliastra\xc4\x8f\xc5\xbc\xcb\x9de'
      , 'Thaliastra\xdfe'
      )
    , ( b'F\xc4\x8f\xc5\xbc\xcb\x9dnfhaus'
      , 'F\xfcnfhaus'
      )
    , ( b'Putzingerstra\xc4\x8f\xc5\xbc\xcb\x9de'
      , 'Putzingerstra\xdfe'
      )
    , ( b'H\xc4\x8f\xc5\xbc\xcb\x9dtteldorf'
      , 'H\xfctteldorf'
      )
    , ( b'Hollandstra\xc4\x8f\xc5\xbc\xcb\x9de'
      , 'Hollandstra\xdfe'
      )
    , ( b'Margareteng\xc4\x8f\xc5\xbc\xcb\x9drtel'
      , 'Margareteng\xfcrtel'
      )
    )

class SQL_character (SQL_Type) :

    """ Get string from sql dump and convert to unicode.
    >>> sq = SQL_character ()
    >>> for k, v in broken_strings_utf8 :
    ...     if sq (k) != v :
    ...         print (repr (sq (k)), repr (v))
    >>> sq.charset = 'latin1'
    >>> for k, v in broken_strings_latin1 :
    ...     if sq (k) != v :
    ...         print (repr (sq (k)), repr (v))
    >>> sq.charset = 'utf-8'
    >>> sq.fix_double_encode = True
    >>> for k, v in broken_strings_utf8_double :
    ...     if sq (k) != v :
    ...         print (repr (sq (k)), repr (v))
    """

    charset = 'utf-8'
    fix_double_encode = False # enabling this makes sense only for utf-8
    re_double = re.compile (r'\xc3\x83|\x82\xc2|\xc5|\xc4\x82')

    def __call__ (self, s) :
        if s == b'\\N' or s == b'NULL' :
            return None
        if self.charset == 'utf-8' and self.fix_double_encode :
            # Don't know how these happen -- seen in the wild
            if b'\xc3\x83' in s :
                s = s.replace (b'\xc3\x83\xc5\xb8', b'\xc3\x83\xc2\x9f')     # ß
                s = s.replace (b'\xc3\x83\xc5\x93', b'\xc3\x83\xc2\x9c')     # Ü
                s = s.replace (b'\xc3\x83\xe2\x80\x93', b'\xc3\x83\xc2\x96') # Ö
            if b'\x82\xc2' in s :
                s = s.replace (b'\xc4\x82\xc2\xb6', b'\xc3\x83\xc2\xb6')     # ö
                s = s.replace (b'\xc4\x82\xc2\xa4', b'\xc3\x83\xc2\xa4')     # ä

            if b'\xc4\x82' in s :
                s = s.replace (b'\xc4\x82\xe2\x80\x93', b'\xc3\x83\xc2\x96') # Ö
                s = s.replace (b'\xc4\x82\xc5\xba', b'\xc3\x83\xc2\x9f')     # ß
                s = s.replace (b'\xc4\x82\xc4\xbd', b'\xc3\x83\xc2\xbc')     # ü

            if b'\xc5' in s :
                # mangled beyond repair, use context:
                s = s.replace \
                    ( b'stra\xc4\x8f\xc5\xbc\xcb\x9de'
                    , b'stra\xc3\x83\xc2\x9fe'
                    ) # straße
                s = s.replace \
                    ( b'g\xc4\x8f\xc5\xbc\xcb\x9drtel'
                    , b'g\xc3\x83\xc2\xbcrtel'
                    ) # gürtel
                s = s.replace \
                    ( b'F\xc4\x8f\xc5\xbc\xcb\x9dnfhaus'
                    , b'F\xc3\x83\xc2\xbcnfhaus'
                    ) # Fünfhaus
                s = s.replace \
                    ( b'M\xc4\x8f\xc5\xbc\xcb\x9dller'
                    , b'M\xc3\x83\xc2\xbcller'
                    ) # Müller
                s = s.replace \
                    ( b'H\xc4\x8f\xc5\xbc\xcb\x9dttel'
                    , b'H\xc3\x83\xc2\xbcttel'
                    ) # Hüttel

            if b'\xc3\xa2\xe2\x82' in s :
                s = s.replace \
                    ( b'\xc3\xa2\xe2\x82\xac\xe2\x80\x9c'
                    , b'\xc3\xa2\xc2\x80\xc2\x93'
                    ) # probably an N-Dash
            try :
                return s.decode ('utf-8').encode ('latin1').decode ('utf-8')
            except UnicodeDecodeError :
                pass
        return s.decode (self.charset)
    # end def __call__

    def format (self, dialect, typ, value) :
        if value is None :
            return dialect.sql_null
        return value
    # end def format

# end class SQL_character
SQL_enum = SQL_text = SQL_varchar = SQL_character

class SQL_Time_Without_Zone (SQL_Type) :
    """ convert sql timestamp with time zone.
    >>> t = SQL_Time_Without_Zone ()
    >>> t ("00:00:00")
    datetime.time(0, 0)
    >>> t ("17:05:16.609")
    datetime.time(17, 5, 16, 609000)
    >>> t ("17:05:16")
    datetime.time(17, 5, 16)
    >>> t ("17:43:33")
    datetime.time(17, 43, 33)
    """

    timefmt = '%H:%M:%S.%f'

    def __call__ (self, ts) :
        if ts == '\\N' or ts == 'NULL' :
            return None
        fmt = self.timefmt
        if len (ts) == 8 :
            fmt = '%H:%M:%S'
        d = datetime.strptime (ts, fmt)
        return d.time ()
    # end def __call__

# end class SQL_Time_Without_Zone

class SQL_Timestamp_Without_Zone (SQL_Type) :
    """ convert sql timestamp with time zone.
    >>> ts = SQL_Timestamp_Without_Zone ()
    >>> ts ("0000-00-00 00:00:00")
    >>> ts ("2012-05-24 17:05:16.609")
    datetime.datetime(2012, 5, 24, 17, 5, 16, 609000)
    >>> ts ("2012-05-24 17:43:33")
    datetime.datetime(2012, 5, 24, 17, 43, 33)
    """

    timefmt = '%Y-%m-%d %H:%M:%S.%f'

    def __call__ (self, ts) :
        if isinstance (ts, type (b'')) :
            ts = ts.decode ('ascii')
        if ts == '\\N' or ts == 'NULL' or ts == '0000-00-00 00:00:00' :
            return None
        fmt = self.timefmt
        if len (ts) == 19 :
            fmt = '%Y-%m-%d %H:%M:%S'
        return datetime.strptime (ts, fmt)
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

    def format (self, dialect, typ, value) :
        if value is None :
            return dialect.sql_null
        s = self.__super.format (dialect, typ, value)
        return s + value.strftime ('%Z')
    # end def format

# end class SQL_Timestamp_With_Zone

class SQL_date (SQL_Type) :
    """ convert sql date.
    >>> dt = SQL_date ()
    >>> dt ("2011-12-01")
    datetime.date(2011, 12, 1)
    """

    dtfmt = "%Y-%m-%d"

    def __call__ (self, dt) :
        if dt == '\\N' or dt == 'NULL' or dt == '0000-00-00' :
            return None
        d  = datetime.strptime (dt, self.dtfmt)
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
    """ A dictionary that is a little more tolerant *and* is able to
        access elements with an attribute access.
    """

    def __init__ (self, *args, **kw) :
        self.done = False
        dict.__init__ (self, *args, **kw)
    # end def __init__

    def __getattr__ (self, key) :
        if key.startswith ('public') :
            key = key.split ('.', 1) [-1]
        for k in key, 'public.' + key :
            if k in self :
                return self [k]
            if isinstance (k, ustr) :
                k = k.encode ('utf-8')
                if k in self :
                    return self [k]
        raise AttributeError (key)
    # end def __getattr__

    def __setattr__ (self, key, value) :
        if isinstance (key, ustr) :
            key = key.encode ('utf-8')
        self [key] = value
    # end def __setattr__

    def set_done (self, done = True) :
        self.done = done
    # end def set_done

# end class adict

class ACL (autosuper) :

    def __init__ (self) :
        self.revoke = []
        self.grant  = []
    # end def __init__

    def append_revoke (self, name, schema, frm) :
        self.revoke.append ((name, schema, frm))
    # end def append_revoke

    def append_grant (self, name, schema, to) :
        self.grant.append ((name, schema, to))
    # end def append_grant

    def as_pgsql (self) :
        r = []
        if self.grant or self.revoke :
            r.append (b'--')
            x = []
            x.append (b'-- Name: public')
            x.append (b'Type: ACL')
            x.append (b'Schema: -')
            x.append (b'Owner: postgres')
            r.append (b'; '.join (x))
            r.append (b'--')
            r.append (b'')
        for (name, schema, frm) in self.revoke :
            r.append \
                ( b'REVOKE %s ON SCHEMA %s FROM %s;'
                % (name, schema, frm)
                )
        for (name, schema, to) in self.grant :
            r.append \
                ( b'GRANT %s ON SCHEMA %s TO %s;'
                % (name, schema, to)
                )
        if self.grant or self.revoke :
            r.append (b'')
            r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

# end class ACL

class Name_Item (autosuper) :
    name_re = re.compile (b'[^a-zA-Z0-9_]')

    # Probably lots of keywords missing
    keywords = dict.fromkeys \
        ((b'time', b'order', b'position', b'interval', b'null', b'update'))

    def __init__ (self, name) :
        self.with_schema = False
        self.name = name
        self.__super.__init__ ()
    # end def __init__

    @property
    def quoted_name (self) :
        return b"'%s'" % self.name
    # end def quoted_name

    @property
    def quoted_fullname (self) :
        n = self.name
        if self.with_schema :
            n = b'.'.join ((self.schema, self.name))
        return b"'%s'" % n
    # end def quoted_fullname

    @property
    def formatted_name (self) :
        n = self.name
        if self.with_schema :
            n = b'.'.join ((self.schema, self.name))
        if self.name in self.keywords or self.name_re.search (self.name) :
            return b'"%s"' % n
        return n
    # end def formatted_name

    @property
    def short_name (self) :
        if self.name in self.keywords or self.name_re.search (self.name) :
            return b'"%s"' % self.name
        return self.name
    # end def short_name

# end class Name_Item

class Column (Name_Item) :

    def __init__ (self, name, typ, typecl, nullable = True) :
        self.typ       = typ
        self.typecl    = typecl
        self.nullable  = nullable
        self.sequences = []
        self.seq_names = {}
        self.default   = None
        self.__super.__init__ (name)
    # end def __init__

    def append_sequence (self, seq) :
        if seq.name in self.seq_names :
            return
        self.sequences.append (seq)
        self.seq_names [seq.name] = seq
        seq.column = self
    # end def append_sequence

    def as_pgsql (self) :
        r = [self.formatted_name]
        r.append (self.typecl.typ (self.typ))
        if self.default :
            r.append (b'DEFAULT')
            r.append (self.default)
        if not self.nullable :
            r.append (b'NOT NULL')
        return b' '.join (r)
    # end def as_pgsql

# end class Column

class Extension (Name_Item) :

    def __init__ (self, name, schema) :
        self.schema = schema
        self.type   = ''
        self.__super.__init__ (name)
    # end def __init__

    def as_pgsql (self) :
        r = []
        r.append (b'')
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.short_name)
        x.append (b'Type: EXTENSION')
        x.append (b'Schema: -')
        x.append (b'Owner: ')
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        r.append \
            ( b'CREATE EXTENSION IF NOT EXISTS %s WITH SCHEMA %s;'
            % (self.formatted_name, self.schema)
            )
        r.append (b'')
        r.append (b'')
        if self.type :
            r.append (b'--')
            x = []
            x.append (b'-- Name: EXTENSION %s' % self.short_name)
            x.append (b'Type: COMMENT')
            x.append (b'Schema: -')
            x.append (b'Owner: ')
            r.append (b'; '.join (x))
            r.append (b'--')
            r.append (b'')
            r.append \
                ( b"COMMENT ON EXTENSION %s IS '%s';"
                % (self.formatted_name, self.type)
                )
            r.append (b'')
            r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

# end class Extension

class Foreign_Key (Name_Item) :

    def __init__ (self, name, column, key) :
        self.column = column
        self.key    = key
        self.__super.__init__ (name)
    # end def __init__

    def as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.short_name)
        x.append (b'Type: FK CONSTRAINT')
        x.append (b'Schema: %s' % self.table.schema.encode ('utf-8'))
        x.append (b'Owner: %s' % self.table.owner.encode ('utf-8'))
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        r.append (b'ALTER TABLE ONLY %s' % self.table.formatted_name)
        r.append \
            ( b'    ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES '
              b'%s(%s) DEFERRABLE INITIALLY DEFERRED;'
            % ( self.formatted_name
              , self.column.formatted_name
              , self.key.table.formatted_name
              , b', '.join (k.formatted_name for k in self.key.columns)
              )
            )
        r.append (b'')
        r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

# end class Foreign_Key

class Index (Name_Item) :

    def __init__ (self, name, typ, columns, ops) :
        self.typ       = typ
        self.columns   = columns
        self.ops       = ops
        self.is_unique = False
        self.__super.__init__ (name)
    # end def __init__

    def as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.short_name)
        x.append (b'Type: INDEX')
        x.append (b'Schema: %s' % self.table.schema)
        x.append (b'Owner: %s' % self.table.owner)
        if self.table.tspace :
            x.append (b'Tablespace: %s' % self.table.tspace)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        u = b''
        if self.is_unique :
            u = b'UNIQUE '
        r.append \
            ( b'CREATE %sINDEX %s ON %s USING %s (%s);'
            % ( u
              , self.formatted_name
              , self.table.formatted_name
              , self.typ
              , b', '.join (self.col_as_pgsql (c) for c in self.columns)
              )
            )
        r.append (b'')
        r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

    def col_as_pgsql (self, column) :
        name = column.name
        op   = self.ops.get (name, b'')
        if op :
            return b' '.join ((column.formatted_name, op))
        return column.formatted_name
    # end def col_as_pgsql

# end class Index

class Key (Name_Item) :
    """ Uniqueness constraint or primary key
    """

    def __init__ (self, name, typ, columns) :
        self.typ     = typ
        self.columns = columns
        self.__super.__init__ (name)
    # end def __init__

    def as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s %s' % (self.table.short_name, self.short_name))
        x.append (b'Type: CONSTRAINT')
        x.append (b'Schema: %s' % self.table.schema)
        x.append (b'Owner: %s' % self.table.owner)
        if self.table.tspace :
            x.append (b'Tablespace: %s' % self.table.tspace)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        r.append (b'ALTER TABLE ONLY %s' % self.table.formatted_name)
        r.append \
            ( b'    ADD CONSTRAINT %s %s (%s);'
            % ( self.formatted_name
              , self.typ
              , b', '.join (k.formatted_name for k in self.columns)
              )
            )
        r.append (b'')
        r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

# end class Key

class Set_Statement (Name_Item) :

    def __init__ (self, name, value) :
        self.value = value
        self.__super.__init__ (name)
    # end def __init__

    def as_pgsql (self) :
        r = []
        r.append (b'SET %s = %s;' % (self.formatted_name, self.value))
        return b'\n'.join (r)
    # end def as_pgsql

# end class Set_Statement

class DB_Object (Name_Item) :

    def __init__ (self, name) :
        self.owner  = ''
        self.schema = ''
        self.__super.__init__ (name)
        if b'.' in self.name :
            # Should only contain a single dot
            self.schema, self.name = self.name.split (b'.')
            self.with_schema = True
    # end def __init__

    def set_schema (self, schema) :
        if self.schema and schema != self.schema :
            raise Parse_Error \
                ('Duplicate schema %s for table %s' % (schema, self.name))
        self.schema = schema
    # end def set_schema

    def set_owner (self, owner) :
        if self.owner and owner != self.owner :
            raise Parse_Error \
                ('Duplicate owner %s for table %s' % (owner, self.name))
        self.owner = owner
    # end def set_owner

    def owner_as_pgsql (self) :
        r = []
        if self.owner :
            r.append \
                ( b'ALTER TABLE %s.%s OWNER TO %s;'
                % (self.schema, self.name, self.owner)
                )
            r.append (b'')
        return b'\n'.join (r)
    # end def owner_as_pgsql

# end class DB_Object

class Sequence (DB_Object) :

    def __init__ (self, name) :
        self.start = 1
        self.inc   = 1
        self.min   = None
        self.max   = None
        self.cache = 1
        self.value = 0
        self.booly = True
        self.__super.__init__ (name)
    # end def __init__

    def as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.short_name)
        x.append (b'Type: SEQUENCE')
        x.append (b'Schema: %s' % self.schema)
        x.append (b'Owner: %s' % self.owner)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        r.append (b'CREATE SEQUENCE %s' % self.formatted_name)
        r.append (b'    START WITH %d' % self.start)
        r.append (b'    INCREMENT BY %d' % self.inc)
        if self.min is None :
            r.append (b'    NO MINVALUE')
        if self.max is None :
            r.append (b'    NO MAXVALUE')
        r.append (b'    CACHE %d;' % self.cache)
        r.append (b'')
        r.append (self.owner_as_pgsql ())
        if getattr (self, 'column', None) :
            r.append (b'')
            r.append (b'--')
            x = []
            x.append (b'-- Name: %s' % self.short_name)
            x.append (b'Type: SEQUENCE OWNED BY')
            x.append (b'Schema: %s' % self.schema)
            x.append (b'Owner: %s' % self.owner)
            r.append (b'; '.join (x))
            r.append (b'--')
            r.append (b'')
            col = self.column.name
            tbl = self.column.table
            r.append \
                ( b'ALTER SEQUENCE %s OWNED BY %s.%s;'
                % (self.formatted_name, tbl, col)
                )
            r.append (b'')
        r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

    def default_as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.column.short_name)
        x.append (b'Type: DEFAULT')
        x.append (b'Schema: %s' % self.schema)
        x.append (b'Owner: %s' % self.owner)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        r.append \
            (b'ALTER TABLE ONLY %s ALTER COLUMN %s SET DEFAULT '
             b"nextval('%s'::regclass);"
            % ( self.column.table.formatted_name
              , self.column.formatted_name
              , self.formatted_name
              )
            )
        r.append (b'')
        r.append (b'')
        return b'\n'.join (r)
    # end def default_as_pgsql

    def init_as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.short_name)
        x.append (b'Type: SEQUENCE SET')
        x.append (b'Schema: %s' % self.schema)
        x.append (b'Owner: %s' % self.owner)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        tf = [b'false', b'true'][self.booly]
        r.append \
            ( b'SELECT pg_catalog.setval(%s, %d, %s);'
            % (self.quoted_fullname, self.value, tf)
            )
        r.append (b'')
        r.append (b'')
        return b'\n'.join (r)
    # end def init_as_pgsql

# end class Sequence

class Table (DB_Object) :

    def __init__ (self, name) :
        self.owner        = b''
        self.schema       = b''
        self.tspace       = b''
        self.columns      = []
        self.by_col       = {}
        self.contents     = []
        self.keys         = []
        self.key_by_cols  = {}
        self.foreign_keys = []
        self.constraints  = []
        self.indeces      = []
        self.__super.__init__ (name)
    # end def __init__

    def append_column (self, column) :
        self.columns.append (column)
        self.by_col [column.name] = column
        column.table = self
    # end def append_constraint

    def append_constraint (self, line) :
        line = line.rstrip (',')
        self.constraints.append (line)
    # end def append_constraint

    def append_index (self, idx) :
        self.indeces.append (idx)
        idx.table = self
    # end def append_index

    def append_key (self, key) :
        self.keys.append (key)
        cns = tuple (c.name for c in key.columns)
        self.key_by_cols [cns] = key
        key.table = self
    # end def append_key

    def append_foreign (self, key) :
        self.foreign_keys.append (key)
        key.table = self
    # end def append_foreign

    def as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Name: %s' % self.short_name)
        x.append (b'Type: TABLE')
        x.append (b'Schema: %s' % self.schema)
        x.append (b'Owner: %s' % self.owner)
        if self.tspace :
            x.append (b'Tablespace: %s' % self.tspace)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        r.append (b'CREATE TABLE %s (' % self.formatted_name)
        ncol = len (self.columns)
        ident = b'    '
        for n, col in enumerate (self.columns) :
            comma = b','
            if n == ncol - 1 and not self.constraints :
                comma = b''
            r.append (ident + col.as_pgsql () + comma)
        ncol = len (self.constraints)
        for n, cons in enumerate (self.constraints) :
            comma = b','
            if n == ncol - 1 :
                comma = b''
            r.append (ident + cons.encode ('utf-8') + comma)
        r.append (b');')
        r.append (b'')
        r.append (b'')
        r.append (self.owner_as_pgsql ())
        for col in self.columns :
            for s in col.sequences :
                r.append (s.as_pgsql ())
        return b'\n'.join (r)
    # end def as_pgsql

    def content_as_pgsql (self) :
        r = []
        r.append (b'--')
        x = []
        x.append (b'-- Data for Name: %s' % self.short_name)
        x.append (b'Type: TABLE DATA')
        x.append (b'Schema: %s' % self.schema)
        x.append (b'Owner: %s' % self.owner)
        r.append (b'; '.join (x))
        r.append (b'--')
        r.append (b'')
        ffields = [c.formatted_name for c in self.columns]
        r.append \
            ( b'COPY %s (%s) FROM stdin;'
            % (self.formatted_name, b', '.join (ffields))
            )
        for line in self.contents :
            c = []
            for col in self.columns :
                cn = col.name
                v = line [cn]
                if isinstance (v, string_types) :
                    v = v.encode ('utf-8')
                c.append (col.typecl.format (dialect_pg, col.typ, v))
            r.append (b'\t'.join (c))
        r.append (b'\\.')
        r.append (b'')
        r.append (b'')
        for col in self.columns :
            for seq in col.sequences :
                r.append (seq.init_as_pgsql ())
        return b'\n'.join (r)
    # end def content_as_pgsql

    def seq_defaults (self) :
        """ Sequence initializations """
        r = []
        for col in self.columns :
            for seq in col.sequences :
                r.append (seq.default_as_pgsql ())
        return b'\n'.join (r)
    # end def seq_defaults

    def __getitem__ (self, name) :
        return self.by_col [name]
    # end def __getitem__

# end class Table

class SQL_Parser (Parser) :

    # don't convert automagically to unicode
    encoding   = None

    re_charset = re.compile (br'CHARSET=([-a-zA-Z0-9]+)')
    re_copy    = re.compile (br'^COPY\s+(\S+)\s\(([^)]+)\) FROM stdin;$')
    re_endtbl  = re.compile (br'^\).*;$')
    re_func    = re.compile (br'^CREATE FUNCTION ([a-zA-Z0-9]+)\s*\(')
    re_insert  = re.compile \
        (br'INSERT INTO ["`]?([a-z0-9]+)["`]? VALUES \((.*)\);')
    re_table   = re.compile (br'^CREATE TABLE (\S+) \(')
    re_owner   = re.compile (br'^ALTER TABLE (\S+) OWNER TO (\S+);')
    re_ato     = re.compile (br'^ALTER TABLE ONLY (\S+)\s*$')
    re_seq     = re.compile (br'^CREATE SEQUENCE (\S+)')
    re_s_start = re.compile (br'^\s*START WITH (\S+)')
    re_s_inc   = re.compile (br'^\s*INCREMENT BY (\S+)')
    re_s_min   = re.compile (br'^\s*NO MINVALUE')
    re_s_max   = re.compile (br'^\s*NO MAXVALUE')
    re_s_cache = re.compile (br'^\s*CACHE (\S+);')
    re_al_sq   = re.compile (br'^ALTER SEQUENCE (\S+) OWNED BY (\S+);')
    re_sq_set  = re.compile (br"^SELECT pg_catalog.setval"
                             br"\('([^']+)', (\S+), (true|false)\);")
    re_default = re.compile (br"DEFAULT\s+(\S+)")
    re_cons    = re.compile (br'^\s*ADD CONSTRAINT (\S+) '
                             br'(UNIQUE|PRIMARY KEY) \(((\S+\s*)+)\);'
                            )
    re_forgn   = re.compile (br'^\s*ADD CONSTRAINT (\S+) '
                             br'FOREIGN KEY \(([^)]+)\) REFERENCES '
                             br'([^(]+)\(([^)]+)\) DEFERRABLE '
                             br'INITIALLY DEFERRED;'
                            )
    re_index   = re.compile (br'CREATE INDEX (\S+) ON (\S+) USING (\S+) '
                             br'\(([^)]+)\);'
                            )
    re_uindex  = re.compile (br'CREATE UNIQUE INDEX (\S+) ON (\S+) USING (\S+) '
                             br'\(([^)]+)\);'
                            )
    re_set     = re.compile (br'SET (\S+) = ([^;]+);')
    re_ext     = re.compile (br'CREATE EXTENSION IF NOT EXISTS (\S+) '
                             br'WITH SCHEMA (\S+);'
                            )
    re_comment = re.compile (br'COMMENT ON EXTENSION (\S+) '
                             br"IS '([^']+)';"
                            )
    re_revoke  = re.compile (br'REVOKE (\S+) ON SCHEMA (\S+) FROM (\S+);')
    re_grant   = re.compile (br'GRANT (\S+) ON SCHEMA (\S+) TO (\S+);')

    matrix = \
        [ ["init",  re_copy,    "copy",  "copy_start"]
        , ["init",  re_insert,  "init",  "insert"]
        , ["init",  re_func,    "func",  None]
        , ["init",  re_table,   "table", "table_start"]
        , ["init",  re_seq,     "seq",   "seq_start"]
        , ["init",  re_owner,   "init",  "owner"]
        , ["init",  re_al_sq,   "init",  "seq_alter"]
        , ["init",  re_sq_set,  "init",  "seq_setval"]
        , ["init",  re_ato,     "cons",  "cons_start"]
        , ["init",  re_index,   "init",  "create_index"]
        , ["init",  re_uindex,  "init",  "create_uindex"]
        , ["init",  re_set,     "init",  "set_stmt"]
        , ["init",  re_ext,     "init",  "ext_stmt"]
        , ["init",  re_comment, "init",  "ext_comment"]
        , ["init",  re_revoke,  "init",  "revoke_stmt"]
        , ["init",  re_grant,   "init",  "grant_stmt"]
        , ["init",  None,       "init",  None]
        , ["copy",  b'\\.',     "init",  None]
        , ["copy",  None,       "copy",  "copy_entry"]
        , ["cons",  re_cons,    "init",  "cons_end"]
        , ["cons",  re_forgn,   "init",  "foreign_key"]
        , ["func",  b"END;",    "init",  None]
        , ["func",  b"END;$$",  "init",  None]
        , ["func",  None,       "func",  None]
        , ["table", re_endtbl,  "init",  "table_end"]
        , ["table", None,       "table", "table_entry"]
        , ["seq",   re_s_start, "seq",   "seq_startwith"]
        , ["seq",   re_s_inc,   "seq",   "seq_inc"]
        , ["seq",   re_s_min,   "seq",   "seq_min"]
        , ["seq",   re_s_max,   "seq",   "seq_max"]
        , ["seq",   re_s_cache, "init",  "seq_cache"]
        ]

    def __init__ (self, fix_double_encode = False, *args, **kw) :
        self.tables            = adict ()
        self.tablenames        = []
        self.sequences         = adict ()
        self.free_seq          = {}
        self.fix_double_encode = fix_double_encode
        self.objects           = []
        self.extensions        = {}
        self.acl               = ACL ()
        self.droptable         = {}
        self.emptytable        = {}
        self.cb                = {}
        # remember column names in creation order, should really use an
        # OrderedDict in self.tables but this means at least python2.7
        self.columns  = {}
        self.__super.__init__ (*args, **kw)
    # end def __init__

    def register_empty_table (self, tablename) :
        self.emptytable [tablename.encode ('utf-8')] = True
    # end def register_empty_table

    def register_drop_table (self, tablename) :
        self.droptable [tablename.encode ('utf-8')] = True
    # end def register_drop_table

    def register_table_callback (self, tablename, method) :
        self.cb [tablename.encode ('utf-8')] = method
    # end def register_table_callback

    def as_pgsql (self) :
        r = []
        r.append (b'--')
        r.append (b'-- PostgreSQL database dump')
        r.append (b'--')
        r.append (b'')
        for obj in self.objects :
            r.append (obj.as_pgsql ())
        for tn in self.tablenames :
            tbl = self.tables [tn]
            r.append (tbl.as_pgsql ())
        for tn in self.tablenames :
            tbl = self.tables [tn]
            df = tbl.seq_defaults ()
            if df :
                r.append (df)
        for sn in sorted (self.free_seq) :
            seq = self.free_seq [sn]
            r.append (seq.as_pgsql ())
        for tn in self.tablenames :
            tbl = self.tables [tn]
            r.append (tbl.content_as_pgsql ())
        for sn in sorted (self.free_seq) :
            seq = self.free_seq [sn]
            r.append (seq.init_as_pgsql ())
        keys = []
        for tn in self.tablenames :
            tbl  = self.tables [tn]
            keys.extend (tbl.keys)
        for key in sorted (keys, key = lambda x: x.name) :
            r.append (key.as_pgsql ())
        indeces = []
        for tn in self.tablenames :
            tbl  = self.tables [tn]
            indeces.extend (tbl.indeces)
        for idx in sorted (indeces, key = lambda x: x.name) :
            r.append (idx.as_pgsql ())
        fkeys = []
        for tn in self.tablenames :
            tbl  = self.tables [tn]
            fkeys.extend (tbl.foreign_keys)
        for fkey in sorted (fkeys, key = lambda x: x.name) :
            r.append (fkey.as_pgsql ())
        r.append (self.acl.as_pgsql ())
        r.append (b'--')
        r.append (b'-- PostgreSQL database dump complete')
        r.append (b'--')
        r.append (b'')
        return b'\n'.join (r)
    # end def as_pgsql

    def cons_start (self, state, new_state, match) :
        name = match.group (1)
        self.table = self.tables [name]
    # end def cons_start

    def cons_end (self, state, new_state, match) :
        name = match.group (1)
        typ  = match.group (2)
        cns  = match.group (3).split (b',')
        cols = []
        for c in cns :
            c = c.strip ()
            col = self.table [c]
            cols.append (col)
        self.table.append_key (Key (name, typ, cols))
    # end def cons_end

    def copy_entry (self, state, new_state, match) :
        line    = self.line.rstrip (b'\n')
        tbl     = self.table
        fields  = self.fields
        if tbl is None or fields is None :
            return
        dfields = line.split (b'\t')
        # compensate for rstrip
        for x in range (len (fields) - len (dfields)) :
            dfields.append (b'')
        contents = adict \
            ((a, tbl [a].typecl (b)) for a, b in zip (fields, dfields))
        doit = True
        if tbl.name in self.cb :
            doit = self.cb [tbl.name](contents)
        if doit :
            tbl.contents.append (contents)
    # end def copy_entry

    def copy_start (self, state, new_state, match) :
        name  = match.group (1)
        table = self.tables.get (name)
        if not table :
            self.table = self.tablename = self.fields = None
            return
        if table.name in self.droptable or table.name in self.emptytable :
            self.table = self.tablename = self.fields = None
            return
        self.tablename = name
        self.table     = table
        self.fields    = [x.strip (b'"') for x in match.group (2).split (b', ')]
    # end def copy_start

    def create_index (self, state, new_state, match) :
        name = match.group (1)
        tbl  = self.tables.get (match.group (2))
        if not tbl :
            return
        typ  = match.group (3)
        cns  = match.group (4).split (b',')
        cols = []
        ops  = {}
        for c in cns :
            c = c.strip ()
            cops = c.split (b' ', 1)
            op  = b''
            if len (cops) > 1 :
                c = cops [0]
                op = cops [1]
                ops [c] = op
            c = c.strip (b'"')
            col = tbl [c]
            cols.append (col)
        tbl.append_index (Index (name, typ, cols, ops))
    # end def create_index

    def create_uindex (self, state, new_state, match) :
        r = self.create_index (state, new_state, match)
        tbl = self.tables [match.group (2)]
        tbl.indeces [-1].is_unique = True
    # end def create_uindex

    def dump (self) :
        for tn in self.tablenames :
            tbl = self.tables [tn]
            print ("Table: %s" % tbl)
            for line in tbl.contents :
                print ('')
                for k in line :
                    print ("  %s: %s" % (k, repr (line [k])))
    # end dump

    def ext_stmt (self, state, new_state, match) :
        name   = match.group (1)
        schema = match.group (2)
        ext    = Extension (name, schema)
        self.extensions [name] = ext
        self.objects.append (ext)
    # end def ext_stmt

    def ext_comment (self, state, new_state, match) :
        ext  = self.extensions [match.group (1)]
        typ  = match.group (2)
        ext.type = typ
    # end def ext_comment

    def foreign_key (self, state, new_state, match) :
        name = match.group (1)
        col  = self.table [match.group (2)]
        tbl2 = self.tables [match.group (3)]
        col2 = tbl2 [match.group (4)]
        # Get key in original table
        cns  = (col2.name,)
        key  = tbl2.key_by_cols [cns]
        fkey = Foreign_Key (name, col, key)
        self.table.append_foreign (fkey)
    # end def foreign_key

    def grant_stmt (self, state, new_state, match) :
        self.acl.append_grant (*match.groups ())
    # end def grant_stmt

    def insert (self, state, new_state, match) :
        """ This asumes the whole insert statement is one line. """
        name   = match.group (1)
        tpl    = match.group (2).split (b'),(')
        tuples = []
        for t in tpl :
            tuples.append (t.replace (b'\\n', b'\n').replace (b'\\r', b'\r'))
        tbl    = self.tables [name]
        fields = tbl.columns
        reader = csv.reader \
            (tuples, delimiter = ',', quotechar="'", escapechar = '\\')
        for t in reader :
            tbl.contents.append \
                (adict ((a, tbl [a].typecl (b)) for a, b in zip (fields, t)))
    # end def insert

    def owner (self, state, new_state, match) :
        """ Add table or sequence owner, unfortunately sequences are
            also altered by ALTER TABLE
        """
        schema = ''
        name   = match.group (1)
        owner  = match.group (2)
        ename  = name
        if b'.' in name :
            schema, ename = name.rsplit (b'.', 1)
        for n in ename, name :
            for d in self.tables, self.sequences :
                obj = d.get (n, None)
                if obj is not None :
                    obj.set_owner (owner)
                    obj.set_schema (schema)
                    return
    # end def owner

    def revoke_stmt (self, state, new_state, match) :
        self.acl.append_revoke (*match.groups ())
    # end def revoke_stmt

    def seq_alter (self, state, new_state, match) :
        name = match.group (1)
        tbln, coln = match.group (2).split ('.', 1)
        seq = self.sequences [name]
        tbl = self.tables [tbln]
        col = tbl [coln]
        col.append_sequence (seq)
        del self.free_seq [name]
    # end def seq_alter

    def seq_cache (self, state, new_state, match) :
        self.seq.cache = int (match.group (1))
    # end def seq_cache

    def seq_inc (self, state, new_state, match) :
        self.seq.inc = int (match.group (1))
    # end def seq_inc

    def seq_max (self, state, new_state, match) :
        self.seq.max = None
    # end def seq_max

    def seq_min (self, state, new_state, match) :
        self.seq.min = None
    # end def seq_min

    def seq_setval (self, state, new_state, match) :
        name = match.group (1)
        seq  = self.sequences [name]
        seq.value = int (match.group (2))
        seq.booly = (match.group (3) == b'true')
    # end def seq_inc

    def seq_start (self, state, new_state, match) :
        name = match.group (1)
        self.seq = Sequence (name)
        self.sequences [name] = self.seq
        self.free_seq  [name] = self.seq
    # end def seq_start

    def seq_startwith (self, state, new_state, match) :
        self.seq.start = int (match.group (1))
    # end def seq_startwith

    def set_stmt (self, state, new_state, match) :
        name  = match.group (1)
        value = match.group (2)
        s     = Set_Statement (name, value)
        self.objects.append (s)
    # end def set_stmt

    def table_end (self, state, new_state, match) :
        """ End of table may contain charset specification in mysql.
            But the dump is in utf-8 anyway (!)
        """
        m = self.re_charset.search (self.line)
        if self.table is not None :
            for c in self.table.columns :
                if 0 and m :
                    c.charset = m.group (1)
                if self.fix_double_encode :
                    c.typecl.fix_double_encode = True
        self.table = None
    # end def table_end

    def table_entry (self, state, new_state, match) :
        if self.table is None :
            return
        line = self.line.strip ()
        pars = ()
        try :
            name, typ, rest = line.split (None, 2)
        except ValueError :
            name, typ = line.split (None, 1)
            if typ.endswith (b',') :
                typ = typ [:-1]
            rest = b''
        typ  = typ.rstrip (b',')
        rest = rest.rstrip (b',')
        if b'(' in typ :
            pars = typ [typ.index (b'(') + 1:typ.index (b')')].split (b',')
        elif b'(' in rest :
            pars = rest [rest.index (b'(') + 1:rest.index (b')')].split (b',')
        if name.startswith (b'"') or name.startswith (b'`') :
            name = name [1:-1]
        tn = typ.split (b'(', 1) [0]
        if tn == b'character' and rest.startswith (b'varying') :
            tn = b'character varying'
        if rest.startswith (b'with time zone') :
            tn = tn + b' with time zone'
        if rest.startswith (b'without time zone') :
            tn = tn + b' without time zone'
        if typ.startswith (b'int(') or typ.startswith (b'tinyint(') :
            typ = b'integer'
        if typ.startswith (b'varchar') :
            typ = b'varchar'
        if typ.startswith (b'enum') :
            typ = b'enum'
        if typ.startswith (b'numeric') :
            typ = b'numeric'
        if name in (b'PRIMARY', b'UNIQUE') and typ == b'KEY' :
            # FIXME: Should produce a key object
            self.table.append_key (line)
            return
        if name == b'KEY' :
            # FIXME: Should produce a key object
            self.table.append_key (line)
            return
        if name == b'CONSTRAINT' :
            self.table.append_constraint (line)
            return
        t = typ.decode ('ascii')
        r = rest.decode ('ascii')
        method = getattr (self, 'type_' + t, self.type_default)
        nullable = True
        if rest.endswith (b'NOT NULL') :
            nullable = False
        col = Column (name, tn, method (t, r, pars), nullable)
        self.table.append_column (col)
        m = self.re_default.search (rest)
        if m :
            col.default = m.group (1)
    # end def table_entry

    def table_start (self, state, new_state, match) :
        name = match.group (1).strip (b'`')
        tbl  = Table (name)
        if tbl.name in self.droptable :
            self.table = None
        else :
            self.table = self.tables [name] = tbl
            self.tablenames.append (name)
    # end def table_start

    # Magic type methods for SQL types:

    def type_default (self, typ, rest, pars) :
        return globals () ['SQL_' + typ] (*pars)
    # end def type_default

    def type_character (self, typ, rest, pars) :
        assert (rest.startswith ('varying'))
        return self.type_default (typ, rest, pars)
    # end def type_character

    def type_double (self, typ, rest, pars) :
        assert (rest.startswith ('precision'))
        return self.type_default (typ, rest, pars)
    # end def type_double

    def type_time (self, typ, rest, pars) :
        if rest.startswith ('with time zone') :
            return SQL_Time_With_Zone ()
        elif rest.startswith ('without time zone') :
            return SQL_Time_Without_Zone ()
        else :
            raise ValueError ("Invalid timestamp spec: %s" % rest)
    # end def type_time

    def type_timestamp (self, typ, rest, pars) :
        if rest.startswith ('with time zone') :
            return SQL_Timestamp_With_Zone ()
        elif rest.startswith ('without time zone') :
            return SQL_Timestamp_Without_Zone ()
        else :
            raise ValueError ("Invalid timestamp spec: %s" % rest)
    # end def type_timestamp

    def type_datetime (self, typ, rest, pars) :
        return SQL_Timestamp_Without_Zone ()
    # end def type_datetime

    def type_date (self, typ, rest, pars) :
        return SQL_date ()
    # end def type_date

    def type_varchar (self, typ, rest, pars) :
        return self.type_default (typ, rest, pars)
    # end def type_varchar

# end def SQL_Parser

if __name__ == "__main__" :
    if len (sys.argv) > 1 :
        f  = open (sys.argv [1])
    else :
        f = sys.stdin
    c = SQL_Parser ()
    c.parse    (f)
    print (c.as_pgsql ().decode ('utf-8'))
### __END__ sqlparser
