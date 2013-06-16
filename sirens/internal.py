#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-11
@author: shell.xu
'''
import sys

def debug(app, cfg):
    if 'debugfile' in app.cfg:
        debugfile = open(app.cfg['debugfile'], 'w')
    else: debugfile = sys.stdout
    def inner(req):
        print >>debugfile, 'req:', req.url
        for k, v in req.result.iteritems():
            print >>debugfile, 'key:', k
            print >>debugfile, 'value:', v
            print >>debugfile
        print >>debugfile
    return inner
