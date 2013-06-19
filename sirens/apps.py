#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import re, sys, gzip, pprint, logging, cStringIO
from os import path
import yaml, chardet
from lxml import etree, html
import httputils, html_parser, filters, internal
from bases import *

logger = logging.getLogger('application')

class ParseError(StandardError): pass

def lxmlwrap(app, *funcs):
    def inner(worker, req, resp):
        resp.encoding = chardet.detect(resp.content)['encoding']
        doc = html.fromstring(resp.text)
        for func in funcs: func(worker, req, doc)
    return app.http(inner)

class Application(RegNameClsBase):
    lxmlproc = {}
    httpproc = {}
    keyset = set()

    def __init__(self, filepath):
        self.processors = {}
        self.basedir, self.filename = path.split(filepath)
        if self.basedir not in sys.path: sys.path.append(self.basedir)
        with open(filepath) as fi: self.cfg = yaml.load(fi.read())

        if 'result' in self.cfg:
            self.result = self.loadfunc(self.cfg['result'], None)
        if 'disable_robots' not in self.cfg:
            self.accessible = httputils.accessible
        else: self.accessible = lambda url: True
        self.limit = None
        if 'interval' in self.cfg:
            self.limit = httputils.SpeedLimit(self.cfg['interval'])
        self.http = httputils.HttpHub(self.cfg)

        for proccfg in self.cfg['patterns']:
            assert 'name' in proccfg, 'without name'
            self.processors[proccfg['name']] = self.loadaction(proccfg)
        del self.cfg['patterns']

    def result(self, req): print req

    def __call__(self, worker, req):
        if self.limit is not None: self.limit.get(req.url)
        if ':' in req.procname:
            proc = self.loadfunc(req.procname, None)
            assert proc, "unkown python function"
        else:
            assert req.procname in self.processors, "unknown processor name"
            proc = self.processors[req.procname]
        req.result = {}
        proc(worker, req)
        if req.result: self.result(req)

    def loadaction(self, proccfg):
        procs = set_appcfg(self, proccfg, self.lxmlproc)
        if procs: return lxmlwrap(self, *procs)
        procs = set_appcfg(self, proccfg, self.httpproc)
        if procs: return self.http(*procs)
        if 'url' in p: return self.loadfunc(p['url'], None)
        raise ParseError('no handler for match')

    def loadfunc(self, name, cfg):
        if name is None: return None
        modname, funcname = name.split(':')
        if not modname: modname = self.cfg['file']
        if modname == 'internal': return getattr(internal, funcname)
        return getattr(__import__(modname), funcname)(self, cfg)

@Application.register('lxmlproc', 'lxml')
def flxml(app, cmdcfg, cfg): return app.loadfunc(cmdcfg, cfg)

@Application.register('lxmlproc')
def parsers(app, cmdcfg, cfg):
    ps = [mkparser(app, c, cfg) for c in cmdcfg]
    def inner(worker, req, doc):
        for p in ps: p(worker, req, doc)
    return inner

def mkparser(app, cmdcfg, cfg):
    keys = set(cmdcfg.keys())
    secs = []
    for cls in [filters.LinkFilter, filters.ResultFilter]:
        if cls.keyset & keys: secs.append(cls(app, cmdcfg))
    cls = filters.TxtFilter
    if cls.keyset & keys: secs = [cls(app, cmdcfg, *secs),]
    cls = html_parser.LxmlTostring
    assert cls.keyset & keys, "no to string keyword"
    sec = cls(app, cmdcfg, *secs)
    cls = html_parser.LxmlSelector
    assert cls.keyset & keys, "no selector"
    return cls(app, cmdcfg, sec)

@Application.register('httpproc', 'http')
def fhttp(app, cmdcfg, cfg): return app.loadfunc(cmdcfg, cfg)

@Application.register('httpproc', 'download')
def fdownload(app, cmdcfg, cfg):
    if not cmdcfg: cmdcfg = app.cfg.get('download')
    if cmdcfg: download = app.loadfunc(cmdcfg, cfg)
    else:
        assert 'downdir' in app.cfg, 'no download setting, no downdir'
        downdir = app.cfg['downdir']
        def download(worker, req, resp):
            filepath = path.join(downdir, path.basename(req.url))
            with open(filepath, 'wb') as fo: fo.write(resp.content)
    return download

@Application.register('httpproc')
def sitemap(app, cmdcfg, cfg):
    keys = set(cmdcfg.keys())
    cls = filters.LinkFilter
    assert cls.keyset & keys, "no link processor in sitemap"
    sec = cls(app, cmdcfg)
    cls = filters.TxtFilter
    if cls.keyset & keys: sec = cls(app, cmdcfg, sec)

    def inner(worker, req, resp):
        doc = etree.fromstring(
            gzip.GzipFile(
                fileobj=cStringIO.StringIO(resp.content)).read())
        for loc in doc.xpath('ns:url/ns:loc', namespaces={
                'ns':'http://www.sitemaps.org/schemas/sitemap/0.9'}):
            sec(worker, req, None, loc.text)
    return inner
