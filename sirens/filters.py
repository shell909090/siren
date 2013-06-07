#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import re, os, sys, itertools
from urlparse import urljoin
import httputils

class TxtFilter(object):
    filters = {}
    keyset = set()

    def __init__(self, app, cfg, p):
        self.cfg, self.p = cfg, p
        self.filter = self.findset(self.filters)
        self.before = app.loadfunc(cfg.get('before'))
        self.after = app.loadfunc(cfg.get('after'))
        self.map = app.loadfunc(cfg.get('map'))

    def findset(self, d):
        keys = set(self.cfg.keys()) & set(d.keys())
        return [d[key](self.cfg[key]) for key in keys]

    @classmethod
    def register(cls, funcname=None):
        def inner(func):
            fn = funcname or func.__name__
            cls.filters[fn] = func
            cls.keyset.add(fn)
            return func
        return inner

    def __call__(self, req, resp, m):
        for s in self.p(req, resp, m):
            if any(itertools.imap(lambda f: f(s), self.filter)): continue
            if self.before and self.before(s): continue
            if self.map: s = self.map(s)
            yield s
            if self.after and self.after(s): break

@TxtFilter.register('is')
def fis(p):
    reis = re.compile(p)
    return lambda s: not reis.match(s)

@TxtFilter.register()
def isnot(p):
    reisnot = re.compile(p)
    return lambda s: reisnot.match(s)

def absolute_url(url, i):
    if i.startswith('http'): return i
    return urljoin(url, i)

class LinkFilter(object):
    urlfilters = {}
    reqfilters = {}
    keyset = set()

    def __init__(self, app, cfg, p):
        self.cfg, self.p = cfg, p
        print cfg
        self.ufs = self.findset(self.urlfilters)
        self.rfs = self.findset(self.reqfilters)

    def findset(self, d):
        keys = set(self.cfg.keys()) & set(d.keys())
        return [d[key](self.cfg[key]) for key in keys]

    @classmethod
    def register(cls, name, funcname=None):
        l = getattr(cls, name)
        def inner(func):
            fn = funcname or func.__name__
            l[fn] = func
            cls.keyset.add(fn)
            return func
        return inner

    def __call__(self, req, resp, m):
        for s in self.p(req, resp, m):
            url = absolute_url(req.url, s)
            for uf in self.ufs: url = uf(url)
            req = httputils.ReqInfo(url)
            for rf in self.rfs: req = rf(req)
            print req
            yield req

@LinkFilter.register('reqfilters')
def callto(p):
    def inner(req):
        req.callto = p
        return req
    return inner
