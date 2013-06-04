#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import os, sys, logging
import beanstalk
import gevent

logger = logging.getLogger('manager')

def min(msgs):
    if len(msgs) == 1: return msgs[0]
    l, m = None, None
    for msg in msgs:
        if l is None or msg.tasklen() < l:
            m, l = msg, msg.len()
    return m

class Manager(object):

    def __init__(self, host, port=14711):
        self.queue = beanstalkc.Connection(host=host, port=port)
        self.queue.use('queue')
        self.pipes = beanstalkc.Connection(host=host, port=port)
        self.pipes.ignore('default')
        self.workers = []

    def append(self, name):
        self.workers.append(name)

    def run(self):
        while True:
            job = self.queue.get()
            logger.debug('get: %s' % str(req))
            # limiter
            msg = min(self.msgs)
            msg.send(req)

    def request(self, url, headers=None, body=None, method="GET"):
        self.queue.put(url)
