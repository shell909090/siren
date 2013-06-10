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

logger = logging.getLogger('application')

class ParseError(StandardError): pass

def findset(app, cfg, d):
    keys = set(cfg.keys()) & set(d.keys())
    return [d[key](app, cfg[key], cfg) for key in keys]

from httputils import httpwrap

def lxmlwrap(*funcs):
    def inner(worker, req, resp, m):
        resp.encoding = chardet.detect(resp.content)['encoding']
        resp = html.fromstring(resp.text)
        for func in funcs: func(worker, req, resp, m)
    return httpwrap(inner)

class Application(object):
    rules = {}
    lxmls = {}
    https = {}
    keyset = set()

    def __init__(self, filepath, inherit=None):
        self.bases, self.matches = [], []
        self.basedir, self.filename = path.split(filepath)
        self.rules.setdefault(self.filename, {})
        with open(filepath) as fi: self.cfg = yaml.load(fi.read())
        if inherit:
            c = inherit.copy()
            c.update(self.cfg)
            self.cfg = c

        for p in self.cfg['patterns']:
            func = self.loadaction(p)
            if 'id' in p: self.rules[self.filename][p['id']] = func
            if 'base' in p: self.bases.append((p['base'], func, p))
            elif 'match' in p: self.matches.append((re.compile(p['match']), func, p))
            elif 'id' not in p: raise ParseError('unknown patterns')
        del self.cfg['patterns']

        if 'after' in self.cfg:
            self.cfg['after'] = self.loadfunc(self.cfg['after'])
        if 'result' in self.cfg:
            self.result = self.loadfunc(self.cfg['result'])

    @classmethod
    def register(cls, name, funcname=None):
        l = getattr(cls, name)
        def inner(func):
            fn = funcname or func.__name__
            l[fn] = func
            cls.keyset.add(fn)
            return func
        return inner

    def result(self, req, result):
        print req, result

    def __call__(self, worker, req, m=None):
        if req.callto is not None:
            modname = self.filename
            if ':' in req.callto:
                modname, req.callto = req.callto.split(':', 1)
            func = self.rules[modname].get(req.callto)
            if func is None:
                raise Exception('callto function %s not exist in rules.' % cur)
            return func(worker, req, m)
        for b, f, p in self.bases:
            if req.url.startswith(b):
                req.url = req.url[len(b):]
                if 'name' in p: logger.debug('function "%s" runed.' % p['name'])
                return f(worker, req, m)
        for r, f, p in self.matches:
            m = r.match(req.url)
            if 'name' in p: logger.debug('function "%s" runed.' % p['name'])
            if m: f(worker, req, m)

    def loadaction(self, p):
        if 'yaml' in p:
            p = p.copy()
            return Application(path.join(self.basedir, p['yaml']), p)
        if 'redirect' in p:
            def func(worker, req, m): worker.request(p['redirect'])
            return func

        lfuncs = findset(self, p, self.lxmls)
        if lfuncs: return lxmlwrap(*lfuncs)
        lfuncs = findset(self, p, self.https)
        if lfuncs: return httpwrap(*lfuncs)

        if 'url' in p: return self.loadfunc(p['url'])
        raise ParseError('no handler for match')

    def loadfunc(self, name):
        if name is None: return None
        if ':' in name:
            modname, funcname = name.split(':')
        else: modname, funcname = None, name
        if not modname: modname = self.cfg['file']
        basedir = path.dirname(path.realpath(__file__))
        if basedir not in sys.path: sys.path.append(basedir)
        if self.basedir not in sys.path: sys.path.append(self.basedir)
        return getattr(__import__(modname), funcname)

import html_parser, sitemap_parser, filters
def parser_map(app, cfg):
    keys = set(cfg.keys())
    parser = None
    for pcls in [html_parser.LxmlParser,]:
        if pcls.keyset & keys:
            parser = pcls(cfg)
            break
    if parser is None:
        raise ParseError('no parser match for config: %s' % str(cfg))
    for fcls in [filters.TxtFilter,]:
        if fcls.keyset & keys: parser = fcls(app, cfg, parser)
    return parser

@Application.register('lxmls', 'lxml')
def flxml(app, p, cfg): return app.loadfunc(p)

@Application.register('lxmls')
def links(app, p, cfg):
    links = [filters.LinkFilter(app, c, parser_map(app, c)) for c in p]
    def inner(worker, req, resp, m):
        for parser in links:
            for req in parser(req, resp, m): worker.append(req)
    return inner

@Application.register('lxmls')
def result(app, p, cfg):
    result = [(k, parser_map(app, v)) for k, v in p.iteritems()]
    def inner(worker, req, resp, m):
        r = dict((k, list(parser(req, resp, m)))
                 for k, parser in result)
        if 'after' in app.cfg: r = app.cfg['after'](r)
        if r: worker.result(worker, req, r)
    return inner

@Application.register('https', 'http')
def fhttp(app, p, cfg): return app.loadfunc(p)

@Application.register('https', 'download')
def fdownload(app, p, cfg):
    if not p: p = app.cfg.get('download')
    if p: download = app.loadfunc(p)
    else:
        downdir = app.cfg['downdir']
        def download(worker, req, resp, m):
            filepath = path.join(downdir, path.basename(req.url))
            with open(filepath, 'wb') as fo: fo.write(resp)
    return download

@Application.register('https')
def sitemap(app, p, cfg):
    keys = set(p.keys())
    def parser(req, resp, m):
        resp = gzip.GzipFile(fileobj=cStringIO.StringIO(resp.content)).read()
        doc = etree.fromstring(resp)
        for loc in doc.xpath('ns:url/ns:loc', namespaces={
                'ns':'http://www.sitemaps.org/schemas/sitemap/0.9'}):
            yield loc.text
    for fcls in [filters.TxtFilter,]:
        if fcls.keyset & keys: parser = fcls(app, p, parser)
    parser = filters.LinkFilter(app, p, parser)
    def inner(worker, req, resp, m):
        for req in parser(req, resp, m): worker.append(req)
    return inner
