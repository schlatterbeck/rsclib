#!/usr/bin/env python3
# Copyright (C) 2005-23 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import sys
from setuptools import setup, Extension
sys.path.insert (1, '.')
from rsclib import __version__

with open ('README.rst') as f:
    description = f.read ()

license     = 'GNU Library or Lesser General Public License (LGPL)'
download    = 'http://downloads.sourceforge.net/project/rsclib/rsclib'
rq          = '>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4'
setup \
    ( name             = "rsclib"
    , version          = __version__
    , description      = "Misc. basic stuff needed by RSCs tools"
    , long_description = ''.join (description)
    , license          = license
    , author           = "Ralf Schlatterbeck"
    , author_email     = "rsc@runtux.com"
    , packages         = ['rsclib']
    , platforms        = 'Any'
    , url              = "http://rsclib.sourceforge.net/"
    , entry_points     = dict
        ( console_scripts =
            [ "ast_sip_check=rsclib.ast_probe:sip_check"
            , "rsclib-hexdump=rsclib.hexdump:hexdump_cmd"
            , "rsclib-unhexdump=rsclib.hexdump:unhexdump_cmd"
            ]
        )
    , python_requires  = rq
    , download_url     = \
        "%(download)s/%(__version__)s/rsclib-%(__version__)s.tar.gz" % locals ()
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
