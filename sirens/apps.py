#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import re, sys, pprint, logging
from os import path
import yaml, chardet
from lxml import html
from urlparse import urljoin

logger = logging.getLogger('application')

class ParseError(StandardError): pass

from httputils import httpwrap

def lxmlwrap(*funcs):
    def inner(worker, req, resp, m):
        resp.encoding = chardet.detect(resp.content)['encoding']
        resp = html.fromstring(resp.text)
        for func in funcs: func(worker, req, resp, m)
    return httpwrap(inner)

def absolute_url(url, i):
    if i.startswith('http'): return i
    return urljoin(url, i)

import html_parser, filters
def parser_map(app, cfg):
    keys = set(cfg.keys())
    ps = [html_parser.LxmlParser,]
    fs = [filters.TxtFilter,]
    p = None
    for pcls in ps:
        if pcls.keyset & keys:
            p = pcls(cfg)
            break
    if p is None: raise ParseError('no parser match for config: %s' % str(cfg))
    for fcls in fs:
        if fcls.keyset & keys: p = fcls(app, cfg, p)
    return p

class Application(object):

    def __init__(self, filepath, inherit=None):
        self.bases, self.matches = [], []
        self.cfgdir = path.dirname(filepath)
        with open(filepath) as fi: self.cfg = yaml.load(fi.read())
        if inherit:
            c = inherit.copy()
            c.update(self.cfg)
            self.cfg = c

        for p in self.cfg['patterns']:
            func = self.loadaction(p)
            if 'base' in p: self.bases.append((p['base'], func, p))
            elif 'match' in p: self.matches.append((re.compile(p['match']), func, p))
            else: raise ParseError('unknown patterns')
        del self.cfg['patterns']

        if 'after' in self.cfg:
            self.cfg['after'] = self.loadfunc(self.cfg['after'])
        if 'result' in self.cfg:
            self.result = self.loadfunc(self.cfg['result'])

    def result(self, req, result):
        print req, result

    def __call__(self, worker, req, m=None):
        for b, f, p in self.bases:
            if req.url.startswith(b):
                req.url = req.url[len(b):]
                if 'name' in p: logger.debug('%s runed.' % p['name'])
                return f(worker, req, m)
        for r, f, p in self.matches:
            m = r.match(req.url)
            if 'name' in p: logger.debug('%s runed.' % p['name'])
            if m: f(worker, req, m)

    def loadaction(self, p):
        if 'yaml' in p:
            return Application(path.join(self.cfgdir, p['handler']), p)
        if 'redirect' in p:
            def func(worker, req, m): worker.request(p['redirect'])
            return func
        lfuncs = set(('links', 'result', 'lxml')) & set(p.keys())
        if lfuncs:
            l = []
            for key in lfuncs:
                if key == 'links': l.append(self.predef_links(p))
                elif key == 'result': l.append(self.predef_result(p))
                elif key == 'lxml': l.append(self.loadfunc(p['lxml']))
            return lxmlwrap(*l)
        lfuncs = set(('download', 'http')) & set(p.keys())
        if lfuncs:
            l = []
            for key in lfuncs:
                if key == 'download': l.append(self.predef_download(p['download']))
                elif key == 'http': l.append(self.loadfunc(p['http']))
            return httpwrap(*l)
        if 'url' in p: return self.loadfunc(p['url'])
        raise ParseError('no handler for match')

    def predef_download(self, download):
        if not download: download = self.cfg.get('download')
        if download: download = self.loadfunc(download)
        else:
            downdir = self.cfg['downdir']
            def download(worker, req, resp, m):
                filepath = path.join(downdir, path.basename(req.url))
                with open(filepath, 'wb') as fo: fo.write(resp)
        return download

    def predef_links(self, p):
        links = [parser_map(self, cfg) for cfg in p['links']]
        def inner(worker, req, resp, m):
            for parser in links:
                for l in parser(worker, req, resp, m):
                    worker.request(absolute_url(req.url, l))
        return inner

    def predef_result(self, p):
        result = [(k, parser_map(self, v)) for k, v in p['result'].iteritems()]
        def inner(worker, req, resp, m):
            r = dict((k, list(parser(worker, req, resp, m)))
                     for k, parser in result)
            if 'after' in self.cfg: r = self.cfg['after'](r)
            if r: worker.result(req, r)
        return inner

    def loadfunc(self, name):
        if name is None: return None
        if ':' in name:
            modname, funcname = name.split(':')
        else: modname, funcname = None, name
        if not modname: modname = self.cfg['file']
        if self.cfgdir not in sys.path: sys.path.append(self.cfgdir)
        return getattr(__import__(modname), funcname)
