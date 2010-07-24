#!/usr/bin/python
from __future__ import with_statement

import sys
from os.path import join
from scene import Scene, load, ArgsOptions
from pdb import set_trace
from utils import _err_exit

class Octree():
    def __init__(self, sc = None):

        self.vertices = []
        self.bb = None
        self.childs = []

        if sc is not None:
            vertices = []
            for t in sc.index:
                vertices.append( (sc.points[t[0]], t[0]) )
                vertices.append( (sc.points[t[1]], t[1]) )
                vertices.append( (sc.points[t[2]], t[2]) )

            max_depth = 50
            self.root = build(self, sc.bb, vertices, 0, max_depth)

def build(octree, bb, vertices, depth, max_depth):
    octree.bb = bb
    octree.vertices = vertices
    octree.childs = []

    vertices = [v for v in vertices if bb.is_inside(v[0])]
    if len(vertices) > 20 and depth < max_depth:

        childs = []
        for b in bb.split():
            subtree = Octree()
            childs.append( build(subtree, b, vertices, depth + 1, max_depth) )
        octree.childs = childs

    return octree

def main():
    sc = load( join('test', 'data', 'gears.obj') )
    g = Octree(sc)

if __name__ == '__main__':
    main()
    
