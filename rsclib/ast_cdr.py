#!/usr/bin/python

import csv
import time

format = '%Y-%m-%d %H:%M:%S'

class CDR_Parser :
    def __init__ (self, * files) :
        self.files = files
    # end def __init__

    def time_ok (self, t) :
        date = time.strftime ('%Y-%m-%d ', t)
        time_to   = time.strptime (date + self.time_to,   '%Y-%m-%d %H:%M')[3:6]
        time_from = time.strptime (date + self.time_from, '%Y-%m-%d %H:%M')[3:6]
        t         = t [3:6]
        if not time_from or not time_to :
            return True
        if time_from < time_to :
            if not time_from <= t < time_to :
                return False
        else :
            if time_to < t <= time_from :
                return False
        return True
    # end def time_ok

    def sum_over \
        ( self, callee_prefix
        , date_from = None
        , date_to   = None
        , time_from = None
        , time_to   = None
        ) :
        self.time_from = time_from
        self.time_to   = time_to
        if time_from and not time_to or time_to and not time_from :
            raise ValueError, "Specify both or none of time_from, time_to"
        sum = 0
        for f in self.files :
            reader = csv.reader (open (f), dialect = 'excel', delimiter = ',')
            for line in reader :
                if line [14] != 'ANSWERED' :
                    continue
                start = time.strptime (line [10], format)
                end   = time.strptime (line [11], format)
                try :
                    call = line[8].split (':')[1][1:]
                except IndexError :
                    call = ""
                if (   call.startswith (callee_prefix)
                   and (not date_from or date_from < start)
                   and (not date_to   or start     < date_to)
                   and (not time_from or self.time_ok (start))
                   and (not time_to   or self.time_ok (start))
                   ) :
                    sum += time.mktime (end) - time.mktime (start)
        return sum
    # end def sum_over
# end class CDR_Parser

if __name__ == '__main__' :
    import sys
    p = CDR_Parser (* sys.argv [4:])
    f = format.split (' ')[0]
    if sys.argv [1] == 'F' :
        time_from = '18:00'
        time_to   = '08:00'
    elif sys.argv [1] == 'G' :
        time_from = '08:00'
        time_to   = '18:00'
    else :
        time_from = time_to = None
    print p.sum_over \
        ( '1003'
        , date_from = time.strptime (sys.argv [2], f)
        , date_to   = time.strptime (sys.argv [3], f)
        , time_from = time_from
        , time_to   = time_to
        )
