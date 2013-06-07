#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import os, sys

class TxtFilter(object):
    filters = {}

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
            self.filters[fn] = func
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

# FIXME: should filters in html parser?
