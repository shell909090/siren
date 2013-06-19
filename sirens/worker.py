#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import time, logging
import gevent.queue, gevent.pool, beanstalkc
import httputils

logger = logging.getLogger('worker')

class GeventWorker(object):

    def __init__(self, app, size=1):
        self.pool = gevent.pool.Pool(size)
        self.queue = gevent.queue.JoinableQueue()
        self.done = set()
        self.app = app

    def start(self):
        self.pool.spawn(self.run)
        self.pool.join()

    def run(self):
        while not self.queue.empty():
            reqsrc = self.queue.get()
            if reqsrc is None: return
            if not self.queue.empty() and self.pool.free_count() > 0:
                self.pool.spawn(self.run)
            req = httputils.ReqInfo.unpack(reqsrc)
            # FIXME: doing
            if req.url in self.done: continue
            else: self.done.add(req.url)
            logger.info('get: ' + req.url)
            self.app(self, req)
            self.queue.task_done()

    def append(self, req):
        if req.url in self.done: return
        if not self.app.accessible(req.url):
            logger.info('%s not accessible for robots.txt.' % req.url)
            return
        if req.headers and 'headers' in self.app.cfg:
            h = self.app.cfg['headers'].copy()
            h.update(req.headers)
            req.headers = h
        self.queue.put(req.pack())
        logger.info('put: ' + str(req.url))

class BeanstalkWorker(object):

    # put done to redis
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
            logger.info('get: ' + req)
            self.app(self, req)
            job.delete()

    def append(self, req):
        if not self.app.accessible(url):
            logger.info('%s not accessible for robots.txt.' % req.url)
        if req.headers and 'headers' in self.app.cfg:
            h = self.app.cfg['headers'].copy()
            h.update(req.headers)
            req.headers = h
        self.queue.put(req.pack())
        logger.info('put: ' + str(req.url))
