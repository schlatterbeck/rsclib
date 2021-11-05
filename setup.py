#!/usr/bin/env python3
# Copyright (C) 2005-21 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
#
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

try :
    from rsclib.Version import VERSION
except :
    VERSION = None
from distutils.core import setup, Extension

description = []
f = open ('README.rst')
logo_stripped = False
for line in f :
    if not logo_stripped and line.strip () :
        continue
    logo_stripped = True
    description.append (line)

license     = 'GNU Library or Lesser General Public License (LGPL)'
download    = 'http://downloads.sourceforge.net/project/rsclib/rsclib'
rq          = '>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4'
setup \
    ( name             = "rsclib"
    , version          = VERSION
    , description      = "Misc. basic stuff needed by RSCs tools"
    , long_description = ''.join (description)
    , license          = license
    , author           = "Ralf Schlatterbeck"
    , author_email     = "rsc@runtux.com"
    , packages         = ['rsclib']
    , platforms        = 'Any'
    , url              = "http://rsclib.sourceforge.net/"
    , scripts          = [ 'bin/ast_sip_check'
                         , 'bin/rsclib-hexdump'
                         , 'bin/rsclib-unhexdump'
                         ]
    , python_requires  = rq
    , download_url     = \
        "%(download)s/%(VERSION)s/rsclib-%(VERSION)s.tar.gz" % locals ()
    , classifiers      = \
        [ 'Development Status :: 5 - Production/Stable'
        , 'License :: OSI Approved :: ' + license
        , 'Operating System :: OS Independent'
        , 'Programming Language :: Python'
        , 'Intended Audience :: Developers'
        , 'Programming Language :: Python :: 2'
        , 'Programming Language :: Python :: 2.7'
        , 'Programming Language :: Python :: 3'
        , 'Programming Language :: Python :: 3.5'
        , 'Programming Language :: Python :: 3.6'
        , 'Programming Language :: Python :: 3.7'
        , 'Programming Language :: Python :: 3.8'
        , 'Programming Language :: Python :: 3.9'
        ]
    )
