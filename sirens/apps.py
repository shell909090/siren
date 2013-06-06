#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import re, sys, pprint, logging
from os import path
import yaml, chardet, requests
from lxml import html
from lxml.cssselect import CSSSelector
from urlparse import urljoin

import html_parser

logger = logging.getLogger('application')

class ParseError(StandardError): pass

def httpwrap(func):
    def inner(worker, req, m):
        resp = requests.get(req)
        return func(worker, req, resp, m)
    return inner

def lxmlwrap(func):
    def inner(worker, req, m):
        resp = requests.get(req)
        resp.encoding = chardet.detect(resp.content)['encoding']
        resp = html.fromstring(resp.text)
        return func(worker, req, resp, m)
    return inner

def absolute_url(url, i):
    if i.startswith('http'): return i
    return urljoin(url, i)

def parser_map(app, cfg):
    keys = set(cfg.keys())
    l = [html_parser.LxmlParser,]
    for i in l:
        if i.keyset & keys: return i(app, cfg)

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
            if req.startswith(b):
                req = req[len(b):]
                if 'name' in p: logger.debug('%s runed.' % p['name'])
                return f(worker, req, m)
        for r, f, p in self.matches:
            m = r.match(req)
            if 'name' in p: logger.debug('%s runed.' % p['name'])
            if m: f(worker, req, m)

    def loadaction(self, p):
        if 'yaml' in p:
            return Application(path.join(self.cfgdir, p['handler']), p)
        if 'redirect' in p:
            def func(worker, req, m): worker.request(p['redirect'])
            return func
        if 'result' in p or 'links' in p:
            return lxmlwrap(self.predef_main(p))
        if 'lxml' in p: return lxmlwrap(self.loadfunc(p['lxml']))
        if 'download' in p: return httpwrap(self.predef_download(p['download']))
        if 'http' in p: return httpwrap(self.loadfunc(p['http']))
        if 'url' in p: return self.loadfunc(p['url'])
        raise ParseError('no handler for match')

    def predef_download(self, download):
        if not download: download = self.cfg.get('download')
        if download: download = self.loadfunc(download)
        else:
            downdir = self.cfg['downdir']
            def download(worker, req, resp, m):
                filepath = path.join(downdir, path.basename(req))
                with open(filepath, 'wb') as fo: fo.write(resp)
        return download

    def predef_main(self, p):
        result, links = p.get('result'), p.get('links')
        if links: links = [parser_map(self, cfg) for cfg in links]
        if result:
            result = [(k, parser_map(self, v)) for k, v in result.iteritems()]
        def inner(worker, req, resp, m):
            if links:
                for f in links:
                    for l in f(worker, req, resp, m):
                        worker.request(absolute_url(req, l))
            if result:
                r = dict((k, list(v(worker, req, resp, m))) for k, v in result)
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
