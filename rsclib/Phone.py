#!/usr/bin/python
# Copyright (C) 2012-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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
#
# Phone: parse phone numbers

from __future__ import unicode_literals
import os
from   rsclib.autosuper  import autosuper

class Phone (autosuper) :
    """ Parse phone numbers into a generic format.
        Beware: This is specific for Austria.
    >>> Phone ('+43/2243/26465')
    +43/2243/26465
    >>> Phone ('0043224326465')
    +43/2243/26465
    >>> Phone ('02243/26465')
    +43/2243/26465
    >>> Phone ('06506214017')
    +43/650/6214017
    """

    area_austria = dict.fromkeys \
        (( '2243'
         , '2245'
         , '2168'
         , '2230'
         , '2572'
         , '2287'
         , '2165'
         , '2256'
         , '3137'
         , '316'
         , '3456'
        ))
    nan          = dict.fromkeys (('--', 'n/a', 'keine', '007'))
    number_types = \
        { '720' : 'Ortsunabhängig'
        , '780' : 'Kovergenter Dienst'
        , '900' : 'Mehrwertdienst'
        }
    special      = dict.fromkeys \
        (('650', '660', '664', '676', '680', '681', '688', '699'))
    for k in number_types :
        special [k] = True

    def __init__ (self, number, city = 'Wien', type = 'Festnetz') :
        self.is_valid = False
        self.country_code = self.area_code = self.number = self.desc = None
        if not number :
            return
        if number in self.nan :
            return
        num = number.replace (' ', '')
        if num [0] != '0' and num [3] == '-' :
            num = '0' + num
        num = num.replace ('/', '')
        num = num.replace ('-', '')
        num = num.replace ('.', '')
        num = num.replace ('(0)', '')
        num = num.replace ('++', '+')
        num = num.replace ('(', '')
        num = num.replace (')', '')
        if num.startswith ('00') :
            cc = self.country_code = num [2:4]
            if cc == '41' and num [4:6] == '76' :
                self.area_code    = '76'
                self.number       = num [6:]
                self.desc         = 'Mobil'
                self.is_valid     = True
                return
            if cc == '43' :
                rest = num [4:]
            elif num [2:5] in self.special :
                cc   = '43'
                rest = num [2:]
            else :
                raise ValueError ("Number: %s" % number)
        elif num.startswith ('0') :
            cc   = '43'
            rest = num [1:]
        elif num.startswith ('+430') and num [4:7] in self.special :
            cc   = '43'
            rest = num [4:]
        elif num.startswith ('+43') :
            cc   = '43'
            rest = num [3:]
        elif num.startswith ('+31650') :
            self.country_code = '43'
            self.area_code    = '650' # mobile number for netherlands, really
            self.number       = num [6:]
            self.desc         = 'Mobil'
            self.is_valid     = True
            return
        elif len (num) == 7 and city.lower ().startswith ('wien') :
            cc   = '43'
            rest = '1' + num
            if type != 'Fax' :
                type = 'Festnetz'
        elif len (num) == 6 and city.lower ().startswith ('graz') :
            cc   = '43'
            rest = '316' + num
            if type != 'Fax' :
                type = 'Festnetz'
        elif num.startswith ('43') and num [2:5] in self.special :
            cc   = '43'
            rest = num [2:]
        elif num [0:3] in self.special :
            cc   = '43'
            rest = num
        elif '@' in num :
            raise ValueError ("WARN: Email in phone field? %s" % number)
        else :
            raise ValueError ("Number: %s" % number)

        if rest.startswith ('1') :
            area = '1'
            num = rest [1:]
        elif rest [0:3] in self.special :
            area   = rest [0:3]
            type   = self.number_types.get (area, 'Mobil')
            num = rest [3:]
        elif rest [0:4] in self.area_austria :
            area   = rest [0:4]
            if type != 'Fax' :
                type = 'Festnetz'
            num = rest [4:]
        elif rest [0:3] in self.area_austria :
            area   = rest [0:3]
            if type != 'Fax' :
                type = 'Festnetz'
            num = rest [3:]
        else :
            raise ValueError ("Unknown area code: %s" % number)
        self.country_code = cc
        self.area_code    = area
        self.number       = num
        self.desc         = type
        self.is_valid     = True
    # end def __init__

    def __str__ (self) :
        return "+%s/%s/%s" % (self.country_code, self.area_code, self.number)
    # end def __str__
    __repr__ = __str__

    def __iter__ (self) :
        yield self.country_code
        yield self.area_code
        yield self.number
    # end def __iter__

    def __nonzero__ (self) :
        return self.is_valid
    # end def __nonzero__
    __bool__ = __nonzero__

# end class Phone
