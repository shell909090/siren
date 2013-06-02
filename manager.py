#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import os, sys

def min(msgs):
    if len(msgs) == 1: return msgs[0]
    l, m = None, None
    for msg in msgs:
        if l is None or msg.len() < l:
            m, l = msg, msg.len()
    return m

class Manager(object):

    def __init__(self, queue, *msgs):
        self.queue = queue
        self.msgs = msgs

    def run(self):
        while True:
            req = self.queue.get()
            # limiter
            msg = min(self.msgs)
            msg.send(req)

    def request(self, url, headers=None, body=None, method="GET"):
        self.queue.put(url)
