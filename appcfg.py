#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import re, os, sys
import yaml, requests
from lxml import html

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
    def __init__(self, content, inherit=None):
        self.cfg = yaml.load(content)
        if inherit:
            c = inherit.copy()
            c.update(self.cfg)
            self.cfg = c

        self.bases, self.matches = [], []
        for p in self.cfg['patterns']:
            if 'base' in p:
                if 'handler' not in p: raise ParseError('base without handler')
                with open(p['handler']) as fi:
                    self.bases.append((p['base'], Application(fi.read(), p)))
            elif 'match' in p:
                if 'redirect' in p:
                    def func(worker, req, m): worker.request(p['redirect'])
                elif 'http' in p: func = self.loadfunc(p['http'])
                elif 'file' in p: func = httpwrap(self.loadfunc(p['file']))
                elif 'lxml' in p: func = lxmlwrap(self.loadfunc(p['lxml']))
                else: raise ParseError('no handler for match')
                self.matches.append((re.compile(p['match']), func))
            else: raise ParseError('unknown patterns')
        del self.cfg['patterns']

    def loadfunc(self, name):
        modname, funcname = name.split(':')
        if not modname: modname = self.cfg['file']
        return getattr(__import__(modname), funcname)

    def __call__(self, worker, req):
        for b, f in self.bases:
            if req.startswith(b):
                req = req[len(b):]
                return f(worker, req)
        for r, f in self.matches:
            m = r.match(req)
            if m: f(worker, req, m)
