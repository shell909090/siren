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

    def put(self, o):
        logger.debug('put queue')
        self.rds.lpush('queue', o)

    # blocking
    def get(self):
        r = self.rds.blpop('queue')
        logger.debug('get req: %s' % str(r[1]))
        return r[1]

    # def peak(self):
    #     return self.rds.lindex('queue')

class Msg(object):

    def __init__(self, rds, name):
        self.rds, self.name = rds, name
        self.key = 'msg/%s' % name

    def recv(self):
        logger.debug('%s wait' % self.name)
        r = self.rds.blpop(self.key)
        logger.debug('%s get %s' % (self.name, r[1]))
        return r[1]

    # @classmethod
    # def min(self, msgs):
    #     [msg.name for msg in msgs]

    def len(self):
        return self.rds.llen(self.key)

    def send(self, o):
        logger.debug('%s send %s' % (self.name, o))
        self.rds.lpush(self.key, o)

class Sink(object):

    def __init__(self, server, name):
        self.server, self.name = server, name

    def result(self, o):
        pass
