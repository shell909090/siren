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
import httputils

logger = logging.getLogger('application')

class ParseError(StandardError): pass

def findset(app, cfg, d):
    keys = set(cfg.keys()) & set(d.keys())
    return [d[key](app, cfg[key], cfg) for key in keys]

def lxmlwrap(app, *funcs):
    def inner(worker, req, resp, m):
        resp.encoding = chardet.detect(resp.content)['encoding']
        resp = html.fromstring(resp.text)
        for func in funcs: func(worker, req, resp, m)
    return app.http(inner)

class Application(object):
    lxmlproc = {}
    httpproc = {}
    keyset = set()

    def __init__(self, filepath):
        self.processors = {}
        self.basedir, self.filename = path.split(filepath)
        with open(filepath) as fi: self.cfg = yaml.load(fi.read())

        if 'after' in self.cfg:
            self.cfg['after'] = self.loadfunc(self.cfg['after'])
        if 'result' in self.cfg:
            self.result = self.loadfunc(self.cfg['result'])
        if 'disable_robots' not in self.cfg:
            self.accessible = httputils.accessible
        else: self.accessible = lambda url: True
        self.limit = None
        if 'interval' in self.cfg:
            self.limit = httputils.SpeedLimit(self.cfg['interval'])
        self.http = httputils.HttpHub(self.cfg)

        for proccfg in self.cfg['patterns']:
            assert 'name' in p, 'without name'
            self.processors[p['name']] = self.loadaction(proccfg)
        del self.cfg['patterns']

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

    def __call__(self, worker, req, params):
        if self.limit is not None: self.limit.get(req.url)
        # modname = self.filename
        # if ':' in req.callto:
        #     modname, req.callto = req.callto.split(':', 1)
        # func = self.rules[modname].get(req.callto)
        assert func, 'callto function %s not exist in rules.' % cur
        return func(worker, req, m)

    def loadaction(self, proccfg):
        # FIXME:
        # if 'redirect' in proccfg:
        #     def func(worker, req, m):
        #         req = httputils.ReqInfo('', proccfg['redirect'])
        #         worker.append(req)
        #     return func

        procs = findset(self, proccfg, self.lxmlproc)
        if procs: return lxmlwrap(self, *procs)
        procs = findset(self, proccfg, self.httpproc)
        if procs: return self.http(*procs)

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

@Application.register('lxmlproc', 'lxml')
def flxml(app, cmdcfg, cfg): return app.loadfunc(cmdcfg)

@Application.register('lxmlproc')
def links(app, cmdcfg, cfg):
    links = [filters.LinkFilter(app, c, parser_map(app, c)) for c in cmdcfg]
    def inner(worker, req, resp, m):
        for parser in links:
            for req in parser(req, resp, m): worker.append(req)
    return inner

@Application.register('lxmlproc')
def result(app, cmdcfg, cfg):
    # FIXME:
    result = [(k, parser_map(app, v)) for k, v in cmdcfg.iteritems()]
    def inner(worker, req, resp, m):
        r = dict((k, list(parser(req, resp, m)))
                 for k, parser in result)
        if 'after' in app.cfg: r = app.cfg['after'](r)
        if r: worker.result(worker, req, r)
    return inner

@Application.register('httpproc', 'http')
def fhttp(app, cmdcfg, cfg): return app.loadfunc(cmdcfg)

@Application.register('httpproc', 'download')
def fdownload(app, cmdcfg, cfg):
    if not cmdcfg: cmdcfg = cfg.get('download')
    if p: download = app.loadfunc(p)
    else:
        assert 'downdir' in app.cfg, 'no download setting, no downdir'
        downdir = app.cfg['downdir']
        def download(worker, req, resp, m):
            filepath = path.join(downdir, path.basename(req.url))
            with open(filepath, 'wb') as fo: fo.write(resp)
    return download

@Application.register('httpproc')
def sitemap(app, cmdcfg, cfg):
    keys = set(cmdcfg.keys())
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
