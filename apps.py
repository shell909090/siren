#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import re, sys, pprint
from os import path
import yaml, requests
from lxml import html
from lxml.cssselect import CSSSelector

class ParseError(StandardError): pass

def httpwrap(func):
    def inner(worker, req, m):
        resp = requests.get(req)
        return func(worker, req, resp, m)
    return inner

def lxmlwrap(func):
    def inner(worker, req, m):
        resp = requests.get(req)
        resp = html.fromstring(resp.text)
        return func(worker, req, resp, m)
    return inner

class Application(object):

    def __init__(self, filepath, inherit=None):
        self.bases, self.matches = [], []
        self.cfgdir = path.dirname(self.cfgpath)
        with open(filepath) as fi: self.cfg = yaml.load(fi.read())
        if inherit:
            c = inherit.copy()
            c.update(self.cfg)
            self.cfg = c

        for p in self.cfg['patterns']:
            func = self.loadaction(p)
            if 'base' in p: self.bases.append((p['base'], func))
            elif 'match' in p: self.matches.append((re.compile(p['match']), func))
            else: raise ParseError('unknown patterns')
        del self.cfg['patterns']

        pprint.pprint(self.cfg)
        pprint.pprint(self.bases)
        pprint.pprint(self.matches)
        print ''

    def __call__(self, worker, req, m=None):
        for b, f in self.bases:
            if req.startswith(b):
                req = req[len(b):]
                return f(worker, req, m)
        for r, f in self.matches:
            m = r.match(req)
            if m: f(worker, req, m)

    def loadaction(self, p):
        if 'yaml' in p:
            return Application(path.join(self.cfgdir, p['handler']), p)
        if 'redirect' in p:
            def func(worker, req, m): worker.request(p['redirect'])
            return func
        if 'result' in p or 'links' in p:
            return lxmlwrap(self.predef_main(p.get('result'), p.get('links')))
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

    def predef_main(self, result, links):
        if links: links = map(self.loadparser, links)
        if result:
            result = [(k, self.loadparser(v)) for k, v in result.iteritems()]
        def inner(worker, req, resp, m):
            if links:
                for f in links:
                    for l in f(worker, req, resp, m):
                        worker.request(l)
            if result:
                worker.result(req, dict((k, v(worker, req, resp, m))
                                        for k, v in result))
        return inner

    def loadparser(self, p):
        if 'css' in p: sel = CSSSelector(p['css'])
        elif 'xpath' in p: sel = lambda resp: resp.xpath(p['xpath'])
        before = p.get('before')
        after = p.get('after')
        def inner(worker, req, resp, m):
            for i in sel(resp):
                if before and before(i): continue
                yield i
                if after(i): break
        return inner

    def loadfunc(self, name):
        if ':' in name:
            modname, funcname = name.split(':')
        else: modname, funcname = None, name
        if not modname: modname = self.cfg['file']
        return getattr(__import__(modname), funcname)

def main():
    sys.path.append(path.dirname(sys.argv[1]))
    app = Application(sys.argv[1])
    sys.path.pop(-1)

if __name__ == '__main__': main()
