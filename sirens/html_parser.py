#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-06
@author: shell.xu
'''
import os, logging
from lxml import html
from lxml.cssselect import CSSSelector
from bases import *

logger = logging.getLogger('html')

class LxmlSelector(RegClsBase):
    regs = {}
    keyset = set()

    def __init__(self, app, cfg, func):
        self.func = func
        r = set_cmdcfg(cfg, self.regs)
        if len(r) == 0: raise Exception('no html selector')
        if len(r) > 1: raise Exception('more then one html selector')
        self.src = r[0]

    def __call__(self, worker, req, doc):
        for node in self.src(doc):
            logger.debug('%s node selected' % str(node))
            self.func(worker, req, node)

@LxmlSelector.register()
def css(cmdcfg):
    sel = CSSSelector(cmdcfg)
    return lambda doc: sel(doc)

@LxmlSelector.register()
def xpath(cmdcfg):
    return lambda doc: doc.xpath(cmdcfg)

class LxmlTostring(RegClsBase):
    regs = {}
    keyset = set()

    def __init__(self, app, cfg, *funcs):
        self.funcs = funcs
        r = set_cmdcfg(cfg, self.regs)
        if len(r) == 0: raise Exception('no to string translator')
        if len(r) > 1: raise Exception('more then one translator')
        self.tostr = r[0]

    def __call__(self, worker, req, node):
        s = self.tostr(node)
        if not s: return
        logger.debug('node to string: %s' % s)
        for func in self.funcs: func(worker, req, node, s)

@LxmlTostring.register()
def attr(cmdcfg):
    return lambda node: node.get(cmdcfg)

@LxmlTostring.register()
def text(cmdcfg):
    return lambda node: unicode(node.text_content())

@LxmlTostring.register()
def fhtml(cmdcfg):
    return lambda node: html.tostring(node)

# TODO: use python not exe
@LxmlTostring.register()
def html2text(cmdcfg):
    def inner(node):
        fi, fo = os.popen2('html2text -utf8')
        fi.write(html.tostring(node).decode('gbk'))
        fi.close()
        return fo.read()
    return inner
