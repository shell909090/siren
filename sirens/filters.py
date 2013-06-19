#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import re, os, sys, logging, itertools
from urlparse import urljoin
import httputils
from bases import *

logger = logging.getLogger('filters')

class TxtFilter(RegClsBase):
    regs = {}
    keyset = set()

    def __init__(self, app, cfg, *funcs):
        self.funcs = funcs
        self.filter = set_appcfg(app, cfg, self.regs)
        if 'map' in cfg: self.filter.append(eval(cfg['map']))

    def __call__(self, worker, req, node, s):
        logger.debug('string is coming: ' + s)
        for f in self.filter:
            node, s = f(node, s)
            if not s: return logger.debug('failed filter')
        logger.debug('passed filter')
        for func in self.funcs: func(worker, req, node, s)

@TxtFilter.register('is')
def fis(app, cmdcfg, cfg):
    reis = re.compile(cmdcfg)
    return lambda node, s: (node, s) if reis.match(s) else (None, None)

@TxtFilter.register()
def isnot(app, cmdcfg, cfg):
    reisnot = re.compile(cmdcfg)
    return lambda node, s: (None, None) if reisnot.match(s) else (node, s)

@TxtFilter.register()
def dictreplace(app, cmdcfg, cfg):
    r = re.compile(cmdcfg[0])
    return lambda node, s: node, cmdcfg[1].format(**r.match(s).groupdict())

class LinkFilter(RegClsBase):
    regs = {}
    keyset = set()

    def __init__(self, app, cfg):
        self.rfs = set_appcfg(app, cfg, self.regs)

    def __call__(self, worker, req, node, s):
        if s.startswith('//'): s = 'http:' + s
        url = s if s.startswith('http') else urljoin(req.url, s)
        nreq = httputils.ReqInfo(None, url)
        for rf in self.rfs: nreq = rf(nreq, node)
        assert nreq.procname, "dont know which processor to call."
        assert nreq.url, "request without url"
        worker.append(nreq)

@LinkFilter.register()
def call(app, cmdcfg, cfg):
    def inner(req, doc):
        req.procname = cmdcfg
        return req
    return inner

# TODO:
@LinkFilter.register()
def params(app, cmdcfg, cfg):
    def inner(req, doc): return req
    return inner

@LinkFilter.register()
def headers(app, cmdcfg, cfg):
    def inner(req, doc):
        req.headers = cmdcfg
        return req
    return inner

@LinkFilter.register()
def method(app, cmdcfg, cfg):
    cmdcfg = cmdcfg.upper()
    def inner(req, doc):
        req.method = cmdcfg
        return req
    return inner

class ResultFilter(RegClsBase):
    regs = {}
    keyset = set()

    def __init__(self, app, cfg):
        self.result = set_appcfg(app, cfg, self.regs)

    def __call__(self, worker, req, node, s):
        for r in self.result: r(req, s)

@ResultFilter.register()
def result(app, cmdcfg, cfg):
    def inner(req, s):
        req.result.setdefault(cmdcfg, [])
        req.result[cmdcfg].append(s)
    return inner
