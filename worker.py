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

    def __init__(self, name, cfg, host='localhost', port=11300):
        self.queue = beanstalkc.Connection(host=host, port=port)
        self.queue.watch(name)
        self.queue.use(name)
        self.name = name
        self.cfg = cfg

    def run(self):
        while True:
            job = self.queue.reserve(timeout=1)
            if job is None: return

            req = job.body
            logger.debug('get: ' + req)

            self.cfg(self, req)

            # for m, n, p in dispatch(self.cfgs, req):
            #     logger.info('%s run.' % p['handler'])
            #     if m is None: m = []
            #     rslt = p['function'](self, req, *m)
            #     # howto process rslt
            #     logger.info('result: %s' % str(rslt))
            job.delete()

    def request(self, url, headers=None, body=None, method='GET'):
        self.queue.put(url)
        logger.debug('put: ' + str(url))

    def result(self, req, rslt):
        pass

def workgroup(name, funcfile, size=100, host='localhost', port=11300):
    cfgs = loadcfg(funcfile)
    pool = gevent.pool.Pool(size)
    for n in xrange(size): pool.spawn(Worker(name, cfgs).run)
    pool.join()

def load_handler(handler):
    cfgfile = handler['handler']
    with open(cfgfile) as fi: cfg = yaml.load(fi.read())
    patterns = cfg['patterns']
    del cfg['patterns']
    
    for p in patterns:
        if 'redirect' in p:
            lambda 
            p['redirect']
        

def loadcfg(cfgfile):
    with open(cfgfile) as fi: cfg = yaml.load(fi.read())
    sys.path.append(path.dirname(cfgfile))
    cfg['handlers'] = [load_handler(h) for h in cfg['handlers']]

    # for cfg in cfgs:
    #     cfg['base'] = urlparse(cfg['host'])
    #     for p in cfg['patterns']:
    #         modname, funcname = p['handler'].split(':')
    #         if not modname: modname = cfg['file']
    #         p['function'] = getattr(__import__(modname), funcname)
    #         p['re'] = re.compile(p['match'])

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
    # if len(sys.argv) > 2:
    #     for m, n, p in dispatch(cfgs, sys.argv[2]):
    #         print m, n, p

if __name__ == '__main__': main()
