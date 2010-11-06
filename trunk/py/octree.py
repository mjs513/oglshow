#!/usr/bin/python
from __future__ import with_statement

import sys
from os.path import join, exists
from pdb import set_trace
from cPickle import dumps, loads
import zlib

from scene import Scene, load, ArgsOptions
from utils import _err_exit, benchmark
from math_utils import rayIntersectsTriangle, vsub, distance, build_ray

def print_tri(v1, v2, v3):
    print v1[0], v1[1], v1[2], v2[0], v2[1], v2[2], v3[0], v3[1], v3[2]

class Octree():
    __slots__ = ('root', 'bb', 'childs', 'faces')
    def __init__(self, sc=None, fn=None):

        self.vertices = []
        self.bb = None
        self.childs = []

        if sc is not None:
            self.sc = sc
            max_depth = 50
            faces = sc.faces
            self.root = build(self, sc.bb, faces, sc.points, 0, max_depth)

    def load(self, fn):
        with benchmark('deserialize octree'):
            return loads(zlib.decompress(open(fn).read()))

    def dump(self, fn):
        with benchmark('serialize octree'):
            bytes = zlib.compress(dumps(self))
            fo = open(fn, 'w')
            fo.write(bytes)

    def intersect_tris(self, segment):
        def ray_intersect_octree_rec(node, ray, sc):
            ret = []
            if node.bb.intersect(ray):
                if not node.childs:
                    for t in node.faces:
                        v1 = sc.points[t[0]]
                        v2 = sc.points[t[1]]
                        v3 = sc.points[t[2]]
                        intersection = rayIntersectsTriangle(ray[0], ray[1],
                            v1, v2, v3)
                        # print_tri( v1, v2, v3 )
                        # print 'hit ?', intersection
                        if intersection:
                            ret.append( (t, intersection) )

                for child in node.childs:
                    ret.extend( ray_intersect_octree_rec(child, ray, sc) )

            return ret

        ray = build_ray(segment)
        return ray_intersect_octree_rec(self.root, ray, self.root.sc)

    def intersect(self, segment):
        tris = self.intersect_tris(segment)
        if tris:
            return min(tris, key=lambda x: distance(x[1], segment[0]))
        return None

def build(octree, bb, faces, verts, depth, max_depth):
    print 'build', depth, len(faces)
    octree.bb = bb
    octree.childs = []

    # L = len(faces)
    faces = [f for f in faces if bb.intersect_triangle(f, verts)]
    if len(faces) > 10 and depth < max_depth:

        childs = []
        for b in bb.split():
            subtree = Octree()
            childs.append( build(subtree, b, faces, verts, depth + 1, max_depth) )
        octree.childs = childs

    else: # terminal node, attach verts
        octree.faces = faces

    return octree

def main():
    gears = join('test', 'data', 'gears.obj')
    fn = gears
    if len(sys.argv) > 1:
        fn = sys.argv[1]

    sc = load(fn)
    with benchmark('build octree'):
        octree = Octree(sc)

    ray = (octree.bb.min(), octree.bb.max())
    with benchmark('ray octree'):
        print octree.intersect(ray)

    # debug 
    if fn == gears:
        segment = ([6.0124801866126916, -0.51249832634225589, -9.7930512397503584], (5.9371910904864844, -0.50190367657896617, -10.093763375438117))
        assert octree.intersect(segment)

    octree.write()

if __name__ == '__main__':
    main()
    
