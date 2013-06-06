#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-06
@author: shell.xu
'''
import re, os, logging, itertools
from lxml import html
from lxml.cssselect import CSSSelector

logger = logging.getLogger('html')

class LxmlParser(object):
    sources = {}
    tostrs = {}
    filters = {}
    keyset = set()

    def __init__(self, app, cfg):
        self.cfg = cfg

        self.src = self.findset(self.sources)[0]
        self.tostr = self.findset(self.tostrs)[0]
        self.filter = self.findset(self.filters)
        
        self.before = app.loadfunc(cfg.get('before'))
        self.after = app.loadfunc(cfg.get('after'))
        self.map = app.loadfunc(cfg.get('map'))

    def findset(self, d):
        keys = set(self.cfg.keys()) & set(d.keys())
        return [d[key](self.cfg[key]) for key in keys]

    @classmethod
    def register(cls, name, funcname=None):
        l = getattr(cls, name)
        def inner(func):
            fn = funcname or func.__name__
            l[fn] = func
            cls.keyset.add(fn)
            return func
        return inner

    def __call__(self, worker, req, resp, m):
        for node in self.src(req, resp, m):
            if self.before and self.before(node): continue
            s = self.tostr(node)
            if not s: continue
            if any(itertools.imap(lambda f: f(s), self.filter)): continue
            if self.map: s = self.map(s)
            yield s
            if self.after and self.after(s): break

@LxmlParser.register('sources')
def css(p):
    sel = CSSSelector(p)
    return lambda req, resp, m: sel(resp)

@LxmlParser.register('sources')
def xpath(p):
    return lambda req, resp, m: resp.xpath(p)

@LxmlParser.register('tostrs')
def attr(p):
    return lambda node: node.get(p)

@LxmlParser.register('tostrs')
def text(p):
    return lambda node: unicode(node.text_content())

@LxmlParser.register('tostrs', 'html')
def fhtml(p):
    return lambda node: html.tostring(node)

@LxmlParser.register('tostrs')
def html2text(p):
    def inner(node):
        fi, fo = os.popen2('html2text -utf8')
        fi.write(html.tostring(node).decode('gbk'))
        fi.close()
        return fo.read()
    return inner

@LxmlParser.register('filters', 'is')
def fis(p):
    reis = re.compile(p)
    return lambda s: not reis.match(s)

@LxmlParser.register('filters')
def isnot(p):
    reisnot = re.compile(p)
    return lambda s: reisnot.match(s)

# FIXME: should filters in html parser?
