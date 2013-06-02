#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-06-02
@author: shell.xu
'''
import os, sys
import redis
import manager
import q_redis

def main():
    rds = redis.StrictRedis(host='localhost', port=6379, db=0)
    mgr = manager.Manager(
        q_redis.Queue(rds))
    for url in sys.argv[1:]: mgr.request(url)

if __name__ == '__main__': main()
