#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import logging
import beanstalkc

logger = logging.getLogger('worker')

class Worker(object):

    def __init__(self, app):
        self.queue = []
        self.app = app

    def run(self):
        while True:
            req = self.queue.pop(0)
            if req is None: return
            logger.debug('get: ' + req)
            self.app(self, req)
            job.delete()

    def request(self, url, headers=None, body=None, method='GET'):
        self.queue.append(url)
        logger.debug('put: ' + str(url))

    def result(self, req, rslt):
        pass

class BeanstalkWorker(object):

    def __init__(self, app, name, host, port, timeout=1):
        self.queue = beanstalkc.Connection(host=host, port=port)
        self.queue.watch(name)
        self.queue.use(name)
        self.name, self.app, self.timeout = name, app, timeout

    def run(self):
        while True:
            job = self.queue.reserve(timeout=self.timeout)
            if job is None: return
            req = job.body
            logger.debug('get: ' + req)
            self.app(self, req)
            job.delete()

    def request(self, url, headers=None, body=None, method='GET'):
        self.queue.put(url)
        logger.debug('put: ' + str(url))
