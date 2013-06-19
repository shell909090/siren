#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-19
@author: shell.xu
'''
import re, gzip, logging, cStringIO
from os import path
import chardet
from lxml import etree, html
import html_parser, filters, internal
from bases import *

logger = logging.getLogger('action')

class Action(RegNameClsBase):
    lxmlproc = {}
    httpproc = {}
    keyset = set()

    def __init__(self, app, actioncfg):
        self.app = app
        self.lxmls = list(extendlist(
                set_appcfg(app, actioncfg, self.lxmlproc)))
        self.https = set_appcfg(app, actioncfg, self.httpproc)
        if 'url' in actioncfg:
            self.func = self.loadfunc(actioncfg['url'], None)
        if 'result' in actioncfg:
            self.result = app.loadfunc(actioncfg['result'], actioncfg)
        assert self.lxmls or self.https or self.func, 'no handler for match for action'

    def __call__(self, worker, req):
        if hasattr(self, 'func') and self.func(worker, req): return
        resp = self.app.http.do(req)
        if self.https:
            for func in self.https: func(worker, req, resp)
        if self.lxmls:
            resp.encoding = chardet.detect(resp.content)['encoding']
            doc = html.fromstring(resp.text)
            for func in self.lxmls: func(worker, req, doc)
        if hasattr(self, 'result'): self.result(req)

@Action.register('lxmlproc', 'lxml')
def flxml(app, cmdcfg, cfg): return app.loadfunc(cmdcfg, cfg)

@Action.register('lxmlproc')
def parsers(app, cmdcfg, cfg):
    return [mkparser(app, c, cfg) for c in cmdcfg]

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

@Action.register('httpproc', 'http')
def fhttp(app, cmdcfg, cfg): return app.loadfunc(cmdcfg, cfg)

@Action.register('httpproc', 'download')
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

@Action.register('httpproc')
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
