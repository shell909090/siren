#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-06
@author: shell.xu
'''
import os, logging
from lxml import html
from lxml.cssselect import CSSSelector

logger = logging.getLogger('html')

def findset(cfg, d):
    keys = set(cfg.keys()) & set(d.keys())
    return [d[key](cfg[key]) for key in keys]

class LxmlParser(object):
    sources = {}
    tostrs = {}
    keyset = set()

    def __init__(self, cfg):
        self.cfg = cfg
        self.src = findset(self.cfg, self.sources)[0]
        self.tostr = findset(self.cfg, self.tostrs)[0]

    @classmethod
    def register(cls, name, funcname=None):
        l = getattr(cls, name)
        def inner(func):
            fn = funcname or func.__name__
            l[fn] = func
            cls.keyset.add(fn)
            return func
        return inner

    def __call__(self, req, doc, m):
        for node in self.src(doc):
            s = self.tostr(node)
            if s: yield s

@LxmlParser.register('sources')
def css(p):
    sel = CSSSelector(p)
    return lambda doc: sel(doc)

@LxmlParser.register('sources')
def xpath(p):
    return lambda doc: doc.xpath(p)

@LxmlParser.register('tostrs')
def attr(p):
    return lambda node: node.get(p)

@LxmlParser.register('tostrs')
def text(p):
    return lambda node: unicode(node.text_content())

@LxmlParser.register('tostrs', 'html')
def fhtml(p):
    return lambda node: html.tostring(node)

# TODO: use python not exe
@LxmlParser.register('tostrs')
def html2text(p):
    def inner(node):
        fi, fo = os.popen2('html2text -utf8')
        fi.write(html.tostring(node).decode('gbk'))
        fi.close()
        return fo.read()
    return inner
