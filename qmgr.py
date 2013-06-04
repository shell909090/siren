#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import os, sys, pprint, getopt
import beanstalkc

def list(queue, args):
    print queue.tubes()

def stats(queue, args):
    pprint.pprint(queue.stats())

def tube(queue, args):
    pprint.pprint(queue.stats_tube())

def add(queue, args):
    for url in args:
        queue.put(url)
        print 'put:', url

def drop(queue, args):
    for name in args:
        queue.use(name)
        queue.watch(name)
        while True:
            job = queue.reserve(timeout=1)
            if job is None: break
            job.delete()

cmds=['list', 'stats', 'tube', 'add', 'drop']
def main():
    '''
    -h: help
    -H: hostname
    -p: port
    -q: queue
    '''
    optlist, args = getopt.getopt(sys.argv[1:], 'hH:p:q:')
    optdict = dict(optlist)
    if '-h' in optdict:
        print main.__doc__
        return

    host = optdict.get('-H', 'localhost')
    port = optdict.get('-p', '11300')
    name = optdict.get('-q')
    queue = beanstalkc.Connection(host=host, port=int(port))
    queue.use(name)
    queue.watch(name)

    if args[0] not in cmds:
        print main.__doc__
        return
    else: globals()[args[0]](queue, args[1:])

if __name__ == '__main__': main()
