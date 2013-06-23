#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-24
@author: shell.xu
'''
import sys, pprint, getopt, logging
import beanstalkc
import gevent, gevent.pool, gevent.monkey
import apps, httputils, worker

optlist, args = getopt.getopt(sys.argv[1:], 'f:hH:l:p:q:s:t:')
optdict = dict(optlist)

def queue_init(func):
    def inner(args):
        host = optdict.get('-H', 'localhost')
        port = optdict.get('-p', '11300')
        queue = beanstalkc.Connection(host=host, port=int(port))
    return lambda args: func(queue, args)

@queue_init
def list(queue, args):
    print queue.tubes()

@queue_init
def stats(queue, args):
    name = optdict.get('-q')
    if name is not None:
        pprint.pprint(queue.stats_tube(name))
    else: pprint.pprint(queue.stats())

@queue_init
def add(queue, args):
    name = optdict.get('-q')
    if name: queue.use(name)
    funcname = optdict.get('-f', 'main')
    for url in args:
        queue.put(httputils.ReqInfo(funcname, url).pack())
        print 'put:', url

@queue_init
def drop(args):
    def inner(name):
        queue.use(name)
        queue.watch(name)
        while True:
            job = queue.reserve(timeout=1)
            if job is None: break
            job.delete()
    if '-q' in optdict: inner(optdict['-q'])
    else:
        for name in args: inner(name)

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

def run(args):
    gevent.monkey.patch_all()
    initlog(optdict.get('-l', 'INFO'))
    funcname = optdict.get('-f', 'main')
    size = int(optdict.get('-s', '1'))

    app = apps.Application(args[0])
    url = app.cfg['start'] if len(args) < 2 else args[1]
    worker = worker.GeventWorker(app, size)
    worker.append(httputils.ReqInfo(funcname, url))
    worker.start()

def worker(args):
    gevent.monkey.patch_all()
    initlog(optdict.get('-l', 'INFO'))

    app = apps.Application(args[0])
    size = int(optdict.get('-s', '100'))
    pool = gevent.pool.Pool(size)
    for n in xrange(size):
        pool.spawn(worker.BeanstalkWorker(
                app, optdict['-q'], optdict.get('-H', 'localhost'),
                optdict.get('-p', '11300'), int(optdict.get('-t', '10'))).run)
    pool.join()

cmds=['list', 'stats', 'add', 'drop', 'run', 'worker']
def main():
    '''
    -f: function name
    -h: help
    -H: hostname
    -l: log level, DEBUG default
    -p: port
    -q: queue
    -s: worker number, 1 default
    -t: timeout
    cmds: '''
    if '-h' in optdict or not args or args[0] not in cmds:
        print main.__doc__ + ' '.join(cmds)
        return
    globals()[args[0]](args[1:])

if __name__ == '__main__': main()
