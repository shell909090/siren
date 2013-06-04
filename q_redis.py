#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-01
@author: shell.xu
'''
import os, sys, logging
import redis

logger = logging.getLogger('redis')

class Queue(object):

    def __init__(self, rds):
        self.rds = rds

    def put(self, req):
        logger.debug('put queue: %s' % str(req))
        self.rds.lpush('queue', req)

    # blocking
    def get(self):
        r = self.rds.blpop('queue')
        logger.debug('get req: %s' % str(r[1]))
        return r[1]

    # def peak(self):
    #     return self.rds.lindex('queue')

class Pipe(object):

    def __init__(self, rds, name):
        self.rds, self.name = rds, name
        self.key = 'proc/%s' % name
        self.reqkey = 'req/%s' % name

    def sendtask(self, req):
        # logger.debug('%s send %s' % (self.name, o))
        self.rds.lpush(self.key, req)

    def recvtask(self):
        # logger.debug('%s wait' % self.name)
        r = self.rds.blpop(self.key)
        # logger.debug('%s get %s' % (self.name, r[1]))
        return r[1]

    def tasklen(self):
        return self.rds.llen(self.key)

    # @classmethod
    # def min(self, msgs):
    #     [msg.name for msg in msgs]

    def request(self, url, headers=None, body=None, method=None):
        self.push(url)

    def push(self, req):
        self.rds.lpush(self.reqkey, req)

    def pull(self):
        return self.rds.blpop(self.reqkey)[1]

class Sink(object):

    def __init__(self, server, name):
        self.server, self.name = server, name

    def result(self, o):
        pass
