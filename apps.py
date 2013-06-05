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

def rebase(req, i):
    if i.startswith('http'): return i
    return urljoin(req, i)

def html2text(h):
    fi, fo = os.popen2('html2text -utf8')
    fi.write(h.decode('gbk'))
    fi.close()
    return fo.read()

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
            if 'base' in p: self.bases.append((p['base'], func))
            elif 'match' in p: self.matches.append((re.compile(p['match']), func))
            else: raise ParseError('unknown patterns')
        del self.cfg['patterns']

        if 'after' in self.cfg:
            self.cfg['after'] = self.loadfunc(self.cfg['after'])
        if 'result' in self.cfg:
            self.result = self.loadfunc(self.cfg['result'])

    def result(self, req, result):
        print req, result

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
        if links: links = map(self.loadparser, links)
        if result:
            result = [(k, self.loadparser(v)) for k, v in result.iteritems()]
        def inner(worker, req, resp, m):
            if links:
                for f in links:
                    for l in f(worker, req, resp, m): worker.request(l)
            if result:
                r = dict((k, list(v(worker, req, resp, m))) for k, v in result)
                if 'after' in self.cfg: r = self.cfg['after'](r)
                if r: worker.result(req, r)
        return inner

    def loadparser(self, p):
        if 'css' in p: sel = CSSSelector(p['css'])
        elif 'xpath' in p: sel = lambda resp: resp.xpath(p['xpath'])

        if 'attr' not in p and 'text' not in p and 'html' not in p:
            if 'is' in p: raise ParseError('is not legal without attr or text')
            if 'isnot' in p: raise ParseError('isnot not legal without attr or text')
            if 'rebase' in p: raise ParseError('rebase not legal without attr or text')
        fis = re.compile(p['is']) if 'is' in p else None
        fisnot = re.compile(p['isnot']) if 'isnot' in p else None

        before, fmap, after = p.get('before'), p.get('map'), p.get('after')
        if fmap: fmap = self.loadfunc(fmap)

        def inner(worker, req, resp, m):
            for i in sel(resp):
                if before and before(i): continue

                if 'attr' in p: i = i.get(p['attr'])
                elif 'text' in p: i = unicode(i.text_content())
                elif 'html' in p: i = html.tostring(i)
                elif 'html2text' in p: i = html2text(html.tostring(i))
                if not i: continue

                if 'rebase' in p: i = rebase(req, i)
                if fis and not fis.match(i): continue
                if fisnot and fisnot.match(i): continue
                if fmap: i = fmap(i)

                yield i
                if after and after(i): break

        return inner

    def loadfunc(self, name):
        if ':' in name:
            modname, funcname = name.split(':')
        else: modname, funcname = None, name
        if not modname: modname = self.cfg['file']
        if self.cfgdir not in sys.path: sys.path.append(self.cfgdir)
        return getattr(__import__(modname), funcname)
