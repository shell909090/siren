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
    queue = gevent.queue.JoinableQueue()

    def __init__(self, app):
        self.app = app

    def run(self):
        while not self.queue.empty():
            reqsrc = self.queue.get()
            if reqsrc is None: return
            req = httputils.ReqInfo.unpack(reqsrc)
            logger.debug('get: ' + req.url)
            self.app(self, req)
            self.queue.task_done()
            # time.sleep(2)

    def append(self, req):
        self.queue.put(req.pack())
        logger.debug('put: ' + str(req.url))

    def request(self, url, headers=None, body=None, method='GET', callto=None):
        self.append(httputils.ReqInfo(url, headers, body, method, callto))

    def result(self, req, rslt): self.app.result(req, rslt)

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
            req = ReqInfo.unpack(job.body)
            logger.debug('get: ' + req)
            self.app(self, req)
            job.delete()

    def append(self, req):
        self.queue.put(req.pack())
        logger.debug('put: ' + str(req.url))

    def request(self, url, headers=None, body=None, method='GET', callto=None):
        self.append(httputils.ReqInfo(url, headers, body, method, callto))
