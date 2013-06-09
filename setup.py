#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-05-01
@author: shell.xu
'''
from distutils.core import setup

version = '0.1'
description = 'spider framework and utils'
long_description = ' spider framework and utils written by python'

setup(
    name='siren', version=version,
    description=description, long_description=long_description,
    author='Shell.E.Xu', author_email='shell909090@gmail.com',
    scripts=['siren'], packages=['sirens',])
