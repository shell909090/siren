#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-11
@author: shell.xu
'''
import sys

def debug(worker, req, rslt):
    if not hasattr(worker, 'debugfile'):
        if 'debugfile' in worker.app.cfg:
            worker.debugfile = open(worker.app.cfg['debugfile'], 'w')
        else: worker.debugfile = sys.stdout
    print >>worker.debugfile, 'req:', req.url
    for k, v in rslt.iteritems():
        print >>worker.debugfile, 'key:', k
        print >>worker.debugfile, 'value:', v
        print >>worker.debugfile
    print >>worker.debugfile
