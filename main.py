#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import os, sys, logging
import gevent
from gevent import monkey
import worker
from lxml import html

monkey.patch_all()
logger = logging.getLogger('main')

def initlog(lv, logfile=None):
    rootlog = logging.getLogger()
    if logfile: handler = logging.FileHandler(logfile)
    else: handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s,%(msecs)03d %(name)s[%(levelname)s]: %(message)s',
            '%H:%M:%S'))
    rootlog.addHandler(handler)
    rootlog.setLevel(getattr(logging, lv))

def main():
    initlog('DEBUG')
    # rds = redis.StrictRedis(host='localhost', port=6379, db=0)
    w = worker.Worker('worker1', 'spec/siren.cfg', size=2)
    w.run()

if __name__ == '__main__': main()
