#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import requests

class ReqInfo(object):

    def __init__(self, url, headers, body, method):
        self.url, self.headers, self.body, self.method = url, headers, body, method

    def pack(self):
        return json.dumps((self.url, self.headers, self.body, self.method))

    @classmethod
    def unpack(cls, s):
        return cls(*json.loads(s))

def httpwrap(*funcs):
    def inner(worker, req, m):
        resp = requests.get(req.url)
        for func in funcs: func(worker, req, resp, m)
    return inner
