#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import json, time, logging
from urlparse import urlparse
from robotparser import RobotFileParser
import gevent, requests

logger = logging.getLogger('http')

class ReqInfo(object):

    def __init__(self, procname, url, params=None, headers=None, body=None, method='GET'):
        self.procname, self.url, self.params = procname, url, params
        self.headers, self.body, self.method = headers, body, method

    @classmethod
    def unpack(cls, s): return cls(**json.loads(s))
    def pack(self):
        return json.dumps({
                'procname': self.procname, 'url': self.url, 'params': self.params,
                'headers': self.headers, 'body': self.body, 'method': self.method})

class SpeedLimit(object):

    def __init__(self, interval):
        self.last, self.interval = None, interval

    def get(self, url):
        if self.last is None:
            self.last = time.time()
            return
        while (self.last + self.interval) > time.time():
            gevent.sleep(self.last + self.interval - time.time() + 0.1)
        self.last = time.time()

robots_cache = {}

def accessible(url):
    u = urlparse(url)
    if u.netloc not in robots_cache:
        resp = requests.get('http://%s/robots.txt' % u.netloc)
        rp = RobotFileParser()
        rp.parse(resp.content.splitlines())
        robots_cache[u.netloc] = rp
    return robots_cache[u.netloc].can_fetch('*', url)

class HttpHub(object):
    sessions = {}

    def __init__(self, cfg):
        self.cfg = cfg
        self.timeout = cfg.get('timeout')
        self.headers = cfg.get('headers')

    def __call__(self, *funcs):
        def inner(worker, req, params):
            u = urlparse(req.url)
            if u.netloc not in self.sessions:
                sess = requests.Session()
                sess.headers = self.headers
                self.sessions[u.netloc] = sess
            sess = self.sessions[u.netloc]
            resp = sess.request(
                req.method or 'GET', req.url, data=req.body,
                headers=req.headers, timeout=self.timeout)
            for func in funcs: func(worker, req, resp, params)
        return inner
