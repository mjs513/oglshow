#!/usr/bin/env python
from __future__ import with_statement

import sys
sys.path.insert(0, 'build/lib.macosx-10.5-i386-2.5')
import cobj
from time import time

# Context manager
class benchmark(object):
    def __init__(self, name):
        self.name = name
    def __enter__(self):
        self.start = time()
    def __exit__(self, ty, val, tb):
        end = time()
        print("%s : %0.3f seconds" % (self.name, end-self.start))
        return False

fn = '../test/data/teapot.obj'
fn = '../test/data/dragon.obj'
fn = sys.argv[1]

def bench1():
    def c(fn):
        points, index = cobj.read(fn)

        print index[:20]
        for p in points[:20]:
            print p

    def python(fn):
        points = []
        index = []
        for line in open(fn):
            line = line.strip()
            if line.startswith('#'): continue

            tokens = line.split()
            if line.startswith('v'):
                points.append( map(float, tokens[1:]) )
            elif line.startswith('f'):
                # 1 based array, we use 0 based array
                index.append( map(lambda x: int(x)-1, tokens[1:]) )

        print index[:20]
        for p in points[:20]:
            print p

    with benchmark('C'):
        c(fn)

    with benchmark('python'):
        python(fn)
    
bench1()
