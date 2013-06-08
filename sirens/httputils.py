#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import json
import requests

class ReqInfo(object):

    def __init__(self, url, headers=None, body=None, method='GET', callto=None):
        self.url, self.headers, self.body, self.method = url, headers, body, method
        self.callto = callto

    @classmethod
    def unpack(cls, s): return cls(**json.loads(s))
    def pack(self):
        return json.dumps({'url': self.url, 'headers': self.headers,
                           'body': self.body, 'method': self.method,
                           'callto': self.callto})

def httpwrap(*funcs):
    def inner(worker, req, m):
        resp = requests.get(req.url)
        for func in funcs: func(worker, req, resp, m)
    return inner
