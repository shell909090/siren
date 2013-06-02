#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import re, os, sys, pprint, urllib, logging
from urlparse import urlparse
from os import path
import yaml
import gevent, gevent.pool
import lxml.html

logger = logging.getLogger('worker')

class Worker(object):

    def __init__(self, funcfile, psize=1000):
        self.cfgs = loadcfg(funcfile)
        self.pool = gevent.pool.Pool(psize)

    def do(self, req):
        # do those async
        resp = self.http_client(req)
        resp = self.http_parse(resp)
        for m, n, p in dispatch(self.cfgs, req):
            logger.info('%s:%s run.' % (n, p['funcname']))
            rslt, reqs = p['function'](resp, *m, **p.copy())
            # howto process rslt
            logger.info('result: %s' % str(rslt))
            # send reqs to mgr

    def run(self, msg):
        while True: self.pool.spawn(self.do, msg.recv())

    def http_client(self, req):
        logger.debug('http get: ' + str(req))
        return urllib.urlopen(req).read()

    def http_parse(self, resp):
        logger.debug('http parse length %d' % len(resp))
        return lxml.html.fromstring(resp)

def loadcfg(cfgfile):
    with open(cfgfile) as fi: cfgs = yaml.load(fi.read())
    sys.path.append(path.dirname(cfgfile))
    for cfg in cfgs:
        cfg['module'] = __import__(cfg['file'])
        cfg['base'] = urlparse(cfg['host'])
        for p in cfg['patterns']:
            p['re'] = re.compile(p['match'])
            p['function'] = getattr(cfg['module'], p['funcname'])
    sys.path.pop(-1)
    return cfgs

def dispatch(cfgs, url):
    u = urlparse(url)
    for cfg in cfgs:
        if cfg['base'].netloc != u.netloc: continue
        if cfg['base'].scheme != u.scheme: continue
        for p in cfg['patterns']:
            m = p['re'].match(u.path)
            if m is not None:
                yield m.groups(), cfg['name'], p

def main():
    cfgs = loadcfg(sys.argv[1])
    pprint.pprint(cfgs)
    if len(sys.argv) > 2:
        for m, n, p in dispatch(cfgs, sys.argv[2]):
            print m, n, p

if __name__ == '__main__': main()
