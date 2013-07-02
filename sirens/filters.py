#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-07
@author: shell.xu
'''
import re, os, sys, logging, itertools
from urlparse import urljoin
import httputils
from bases import *

logger = logging.getLogger('filters')

txt_filters = {}
links = {}
results = {}

def setup(env, code, app, cmdcfg):
    code.append('    logger.debug("string is coming: " + s)')
    set_psrcfg(env, code, app, cmdcfg, txt_filters)
    code.append('    logger.debug("passed filter")')

    r = set_psrcfg(env, code, app, cmdcfg, links)
    if len(r) > 0:
        code.append('    assert nreq.procname, "dont know which processor to call."')
        code.append('    assert nreq.url, "request without url"')
        code.append("    worker.append(nreq)")

    set_psrcfg(env, code, app, cmdcfg, results)

@register(txt_filters, 'is')
def fis(env, code, app, cmdcfg, cfg):
    env['reis'] = re.compile(cmdcfg)
    code.append('    if not reis.match(s): continue')

@register(txt_filters)
def isnot(env, code, app, cmdcfg, cfg):
    env['reisnot'] = re.compile(cmdcfg)
    code.append('    if reisnot.match(s): continue')

@register(txt_filters)
def dictreplace(env, code, app, cmdcfg, cfg):
    env['replace_re'] = re.compile(cmdcfg[0])
    env['replace_to'] = cmdcfg[1]
    code.append('    s = replace_to.format(**replace_re.match(s).groupdict())')

@register(txt_filters, 'map')
def fmap(env, code, app, cmdcfg, cfg):
    env['mapfunc'] = app.loadfunc(cmdcfg, cfg)
    code.append('    s = mapfunc(s)')

@register(links)
def call(env, code, app, cmdcfg, cfg):
    env['urljoin'] = urljoin
    env['ReqInfo'] = httputils.ReqInfo
    env['call'] = cmdcfg
    code.append("    if s.startswith('//'): s = 'http:' + s")
    code.append("    url = s if s.startswith('http') else urljoin(req.url, s)")
    code.append("    nreq = ReqInfo(None, url)")
    code.append("    nreq.procname = call")

# TODO:
@register(links)
def params(env, code, app, cmdcfg, cfg):
    pass

@register(links)
def headers(env, code, app, cmdcfg, cfg):
    env['headers'] = cmdcfg
    code.append('    nreq.headers = headers')

@register(links)
def method(env, code, app, cmdcfg, cfg):
    env['method'] = cmdcfg.upper()
    code.append('    nreq.method = method')

@register(results)
def result(env, code, app, cmdcfg, cfg):
    env['result'] = cmdcfg
    code.append('    req.result.setdefault(result, [])')
    code.append('    req.result[result].append(s)')
