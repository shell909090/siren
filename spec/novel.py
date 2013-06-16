#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import os, sys

def result(app, cfg):
    filename = app.cfg.get('output', 'output.txt')
    outfile = open(filename, 'w')
    def inner(req):
        outfile.write('\n%s\n\n' % req.result['title'][0].encode('utf-8'))
        outfile.write('\n%s\n\n' % str(req.result['content'][0]))
    return inner
