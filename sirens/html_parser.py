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

selectors = {}
to_strings = {}

def setup(env, code, app, cmdcfg):
    r = set_psrcfg(env, code, app, cmdcfg, selectors)
    if len(r) == 0: raise Exception('no html selector')
    if len(r) > 1: raise Exception('more then one html selector')
    code.append("    logger.debug('%s node selected' % str(node))")

    r = set_psrcfg(env, code, app, cmdcfg, to_strings)
    if len(r) == 0: raise Exception('no to string translator')
    if len(r) > 1: raise Exception('more then one translator')
    code.append('    if not s: continue')
    code.append("    logger.debug('node to string: %s' % s)")

@register(selectors)
def css(env, code, app, cmdcfg, cfg):
    env['css'] = CSSSelector(cmdcfg)
    code.append('  for node in css(doc):')

@register(selectors)
def xpath(env, code, app, cmdcfg, cfg):
    env['xpath'] = cmdcfg
    code.append('  for node in doc.xpath(xpath):')

@register(to_strings)
def attr(env, code, app, cmdcfg, cfg):
    env['attr'] = cmdcfg
    code.append('    s = node.get(attr)')

@register(to_strings)
def text(env, code, app, cmdcfg, cfg):
    code.append('    s = unicode(node.text_content())')

@register(to_strings, 'html')
def fhtml(env, code, app, cmdcfg, cfg):
    env['html'] = html
    code.append('    html.tostring(node)')

# TODO: use python not exe
@register(to_strings)
def html2text(env, code, app, cmdcfg, cfg):
    env['os'] = os
    env['html'] = html
    code.append("    fi, fo = os.popen2('html2text -utf8')")
    code.append("    fi.write(html.tostring(node).decode('gbk'))")
    code.append("    fi.close()")
    code.append("    s = fo.read()")
