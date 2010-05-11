#!/usr/bin/env python
import sys

'''
Work with bits
'''
def log(n):
    i = 0
    while n > 1:
        n = n >> 1
        i += 1
    print i

log(2)
log(4)
log(8)
log(16)
log(32)

sys.exit(0)

'''
Check that we can create a comprehension list of objects
'''
class Toto:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return '%d %d' % (self.a, self.b)

L = [Toto(a, a) for a in xrange(3)]
for i in L: print i

