#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import os, sys, logging
import gzip, cStringIO
from os import path
import requests
from lxml import etree, html
from lxml.html import clean
from lxml.cssselect import CSSSelector

logger = logging.getLogger('bloger')

def sitemap(worker, req, resp, m):
    base = worker.cfg['base']
    resp = gzip.GzipFile(fileobj=cStringIO.StringIO(resp.content)).read()
    doc = etree.fromstring(resp)
    for loc in doc.xpath('ns:url/ns:loc', namespaces={
            'ns':'http://www.sitemaps.org/schemas/sitemap/0.9'}):
        if not loc.text.startswith(base): continue
        print loc.text
        if loc.text[len(base):] == '/': continue
        worker.request(loc.text)
