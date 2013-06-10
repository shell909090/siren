#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import time, logging
import gevent.queue, beanstalkc
import httputils

logger = logging.getLogger('worker')

class Worker(object):

    def request(self, url, headers=None, body=None, method='GET', callto=None):
        self.append(httputils.ReqInfo(url, headers, body, method, callto))

class GeventWorker(Worker):

    def __init__(self, app):
        self.queue = gevent.queue.JoinableQueue()
        self.done = set()
        self.app = app
        self.result = self.app.result

    def run(self):
        while not self.queue.empty():
            reqsrc = self.queue.get()
            if reqsrc is None: return
            req = httputils.ReqInfo.unpack(reqsrc)
            # FIXME: doing
            if req.url in self.done: continue
            else: self.done.add(req.url)
            logger.debug('get: ' + req.url)
            self.app(self, req)
            self.queue.task_done()

    def append(self, req):
        if req.url in self.done: return
        self.queue.put(req.pack())
        logger.debug('put: ' + str(req.url))

class BeanstalkWorker(Worker):

    # put done to redis
    def __init__(self, app, name, host, port, timeout=1):
        self.queue = beanstalkc.Connection(host=host, port=port)
        self.queue.watch(name)
        self.queue.use(name)
        self.name, self.app, self.timeout = name, app, timeout
        self.result = self.app.result

    def run(self):
        while True:
            job = self.queue.reserve(timeout=self.timeout)
            if job is None: return
            req = ReqInfo.unpack(job.body)
            logger.debug('get: ' + req)
            self.app(self, req)
            job.delete()

    def append(self, req):
        self.queue.put(req.pack())
        logger.debug('put: ' + str(req.url))
