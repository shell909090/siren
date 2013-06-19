#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-05
@author: shell.xu
'''
import sys, logging
from os import path
import yaml
import httputils, actions

logger = logging.getLogger('application')

class ParseError(StandardError): pass

class Application(object):
    loadfunc_cache = {}

    def __init__(self, filepath):
        self.processors = {}
        self.basedir, self.filename = path.split(filepath)
        if self.basedir not in sys.path: sys.path.append(self.basedir)
        with open(filepath) as fi: self.cfg = yaml.load(fi.read())

        if 'result' in self.cfg:
            self.result = self.loadfunc(self.cfg['result'], None)
        if 'disable_robots' not in self.cfg:
            self.accessible = httputils.accessible
        else: self.accessible = lambda url: True
        if 'interval' in self.cfg:
            self.limit = httputils.SpeedLimit(self.cfg['interval'])
        self.http = httputils.HttpHub(self.cfg)

        for proccfg in self.cfg['patterns']:
            assert 'name' in proccfg, 'without name'
            self.processors[proccfg['name']] = actions.Action(self, proccfg)
        del self.cfg['patterns']

    def __call__(self, worker, req):
        if hasattr(self, 'limit'): self.limit.get(req.url)
        if ':' in req.procname:
            proc = self.loadfunc(req.procname, None)
            assert proc, "unkown python function"
        else:
            assert req.procname in self.processors, "unknown processor name"
            proc = self.processors[req.procname]
        req.result = {}
        proc(worker, req)
        if hasattr(self, 'result'): self.result(req)

    def loadfunc(self, name, cfg):
        if name is None: return None
        modname, funcname = name.split(':')
        if not modname: modname = self.cfg['file']
        if modname == 'internal': mod = internal
        else: mod = __import__(modname)
        creator = getattr(mod, funcname)
        if creator not in self.loadfunc_cache:
            self.loadfunc_cache[creator] = creator(self, cfg)
        return self.loadfunc_cache[creator]
