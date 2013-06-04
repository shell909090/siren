#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import re, os, sys, pprint, logging
from urlparse import urlparse
from os import path
import yaml, redis, beanstalkc
import gevent, gevent.pool

logger = logging.getLogger('worker')

class Worker(object):

    def __init__(self, name, funcfile, host='localhost', size=100, port=11300):
        self.queue = beanstalkc.Connection(host=host, port=port)
        self.queue.use('%s' % name)
        self.queue.watch('%s' % name)
        self.name = name
        self.cfgs = loadcfg(funcfile)
        self.pool = gevent.pool.Pool(size)

    def run(self):
        while True:
            job = self.queue.reserve()
            self.pool.spawn(self.async_run, job)

    def async_run(self, job):
        req = job.body
        logger.debug('get: ' + req)
        for m, n, p in dispatch(self.cfgs, req):
            logger.info('%s run.' % p['handler'])
            if m is None: m = []
            rslt, reqs = p['function'](req, *m)
            # howto process rslt
            logger.info('result: %s' % str(rslt))
            if reqs:
                for req in reqs: self.request(req)
        job.delete()

    def request(self, url, headers=None, body=None, method='GET'):
        self.queue.put(url)
        logger.debug('put: ' + str(url))

def loadcfg(cfgfile):
    with open(cfgfile) as fi: cfgs = yaml.load(fi.read())
    sys.path.append(path.dirname(cfgfile))
    for cfg in cfgs:
        cfg['base'] = urlparse(cfg['host'])
        for p in cfg['patterns']:
            modname, funcname = p['handler'].split(':')
            if not modname: modname = cfg['file']
            p['function'] = getattr(__import__(modname), funcname)
            p['re'] = re.compile(p['match'])
    sys.path.pop(-1)
    return cfgs

def dispatch(cfgs, url):
    u = urlparse(url)
    for cfg in cfgs:
        if cfg['base'].netloc != u.netloc: continue
        if cfg['base'].scheme != u.scheme: continue
        if not u.path.startswith(cfg['base'].path): continue
        upath = u.path[len(cfg['base'].path):]
        for p in cfg['patterns']:
            m = p['re'].match(upath)
            if m is not None:
                yield m.groups(), cfg['name'], p

def main():
    cfgs = loadcfg(sys.argv[1])
    pprint.pprint(cfgs)
    if len(sys.argv) > 2:
        for m, n, p in dispatch(cfgs, sys.argv[2]):
            print m, n, p

if __name__ == '__main__': main()
