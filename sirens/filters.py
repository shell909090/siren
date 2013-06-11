#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import re, os, sys, itertools
from urlparse import urljoin
import httputils

def findset(app, cfg, d):
    keys = set(cfg.keys()) & set(d.keys())
    return [d[key](app, cfg[key], cfg) for key in keys]

class TxtFilter(object):
    filters = {}
    keyset = set()

    def __init__(self, app, cfg, p):
        self.cfg, self.p = cfg, p
        self.filter = findset(app, self.cfg, self.filters)
        self.before = app.loadfunc(cfg.get('before'))
        self.after = app.loadfunc(cfg.get('after'))
        self.map = app.loadfunc(cfg.get('map'))

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
def fis(app, p, cfg):
    reis = re.compile(p)
    return lambda s: not reis.match(s)

@TxtFilter.register()
def isnot(app, p, cfg):
    reisnot = re.compile(p)
    return lambda s: reisnot.match(s)

@TxtFilter.register()
def dictreplace(app, p, cfg):
    r = re.compile(p[0])
    return lambda s: p[1].format(**r.match(s).groupdict())

def absolute_url(url, i):
    if i.startswith('http'): return i
    return urljoin(url, i)

class LinkFilter(object):
    # urlfilters = {}
    reqfilters = {}
    keyset = set()

    def __init__(self, app, cfg, p):
        self.cfg, self.p = cfg, p
        # self.ufs = findset(app, self.cfg, self.urlfilters)
        self.rfs = findset(app, self.cfg, self.reqfilters)

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
            # for uf in self.ufs: url = uf(url)
            req = httputils.ReqInfo(url)
            for rf in self.rfs: req = rf(req)
            yield req

@LinkFilter.register('reqfilters')
def callto(app, p, cfg):
    if ':' in p: id = p
    else: id = '%s:%s' % (app.filename, p)
    def inner(req):
        req.callto = id
        return req
    return inner

@LinkFilter.register('reqfilters')
def headers(app, p, cfg):
    def inner(req):
        req.headers = p
        return req
    return inner

@LinkFilter.register('reqfilters')
def method(app, p, cfg):
    p = p.upper()
    def inner(req):
        req.method = p
        return req
    return inner
