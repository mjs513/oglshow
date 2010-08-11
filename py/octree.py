#!/usr/bin/python
from __future__ import with_statement

import sys
from os.path import join
from scene import Scene, load, ArgsOptions
from pdb import set_trace
from utils import _err_exit

from math_utils import rayIntersectsTriangle, vsub

def print_tri(v1, v2, v3):
    print v1[0], v1[1], v1[2], v2[0], v2[1], v2[2], v3[0], v3[1], v3[2]

class Octree():
    def __init__(self, sc = None):

        self.vertices = []
        self.bb = None
        self.childs = []

        if sc is not None:
            self.sc = sc
            vertices = []
            for t in sc.index:
                vertices.append( (sc.points[t[0]], t) )
                vertices.append( (sc.points[t[1]], t) )
                vertices.append( (sc.points[t[2]], t) )

            max_depth = 50
            self.root = build(self, sc.bb, vertices, 0, max_depth)

    def intersect(self, segment):
        def ray_intersect_octree_rec(node, ray, sc):
            ret = False
            if node.bb.intersect(ray):
                if not node.childs:
                    for _, t in node.vertices:
                        v1 = sc.points[t[0]]
                        v2 = sc.points[t[1]]
                        v3 = sc.points[t[2]]
                        intersection = rayIntersectsTriangle(ray[0], ray[1],
                            v1, v2, v3)
                        print_tri( v1, v2, v3 )
                        # print 'hit ?', intersection
                        ret += intersection

                for child in node.childs:
                    ret |= ray_intersect_octree_rec(child, ray, sc)

            return ret
    
        ray = 2*[0.0]
        ray[0] = segment[0]
        ray[1] = vsub(segment[1], segment[0])
        return ray_intersect_octree_rec(self.root, ray, self.root.sc)

def build(octree, bb, vertices, depth, max_depth):
    octree.bb = bb
    octree.childs = []

    vertices = [v for v in vertices if bb.is_inside(v[0])]
    if len(vertices) > 10 and depth < max_depth:

        childs = []
        for b in bb.split():
            subtree = Octree()
            childs.append( build(subtree, b, vertices, depth + 1, max_depth) )
        octree.childs = childs

    else: # terminal node, attach verts
        octree.vertices = vertices

    return octree

def main():
    if len(sys.argv) > 1:
        sc = load( sys.argv[1] )
    else:
        sc = load( join('test', 'data', 'gears.obj') )
    octree = Octree(sc)

    ray = (octree.bb.min(), octree.bb.max())
    print octree.intersect(ray)

if __name__ == '__main__':
    main()
    
