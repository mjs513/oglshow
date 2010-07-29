#!/usr/bin/env python
import sys

from viewer import OglSdk
from scene import load
from math_utils import add_quat, quaternion_to_matrix, multiply_point_by_matrix, common_quaternion_from_angles, sub, add, norm, distance, Trackball, vcross, vnorm, add_quat_wiki
from utils import _err_exit, notYetImplemented, benchmark

def test1():
    scene = load('test/data/gears.obj')
    bb = scene.bb
    print bb
    print bb.sphere_beam()
    print bb.center()
    print scene.views[0]

def test2():
    w, h = 600, 480 
    def glutSwapBuffers(): pass
    sdk = OglSdk(w, h, glutSwapBuffers)
    sdk.load_file('test/data/gears.obj')

    print sdk.scene.views[0]
    sdk.pointer_move('rotate', 100, 120, 110, 130)
    print sdk.scene.views[0]

def test3():
    def compute_normals(sc):
        out = len(sc.points) * [ [.0, .0, .0] ]
        triangle_normals = len(sc.index) * [ [.0, .0, .0] ]

        def hash(p):
            return .11234 * p[0] + .35678 * p[1] + .67257 * p[2]

        from collections import defaultdict
        pt_table = defaultdict(list)

        for i, t in enumerate(sc.index):
            p1 = sc.points[t[0]]
            p2 = sc.points[t[1]]
            p3 = sc.points[t[2]]

            pt_table[hash(p1)].append( (i, p1, t[0]) )
            pt_table[hash(p2)].append( (i, p2, t[1]) )
            pt_table[hash(p3)].append( (i, p3, t[2]) )

            normal = vcross(sub(p2, p1), sub(p3, p1))
            normal = vnorm(normal)

            triangle_normals[i] = normal

        for key, value in pt_table.iteritems():
            # we assume no collisions in the hash
            point_index = value[0][2]
            first_point = value[0][1]

            # compute the normal of each triangles around 
            # TODO should be done just once for each triangle in pre-process
            normals = []

            for t_index, p, _ in value:
                assert p == first_point
                normals.append(triangle_normals[t_index])
            
            N = (
                sum(n[0] for n in normals) / len(normals),
                sum(n[1] for n in normals) / len(normals),
                sum(n[2] for n in normals) / len(normals)
            )
            # print N
            out[point_index] = N

        return out

    scene = load(sys.argv[1])
    with benchmark('compute normals'):
        scene.normals = compute_normals(scene)
    scene.write(sys.argv[2])

def test4():
    scene = load(sys.argv[1])
    scene.write(sys.argv[2])

def test5():
    scene = load(sys.argv[1])
    from geom_ops import compute_normals
    with benchmark('compute normals'):
        scene.normals = compute_normals(scene)
    scene.write(sys.argv[2])

def test6():
    from math_utils import rayIntersectsTriangle
    print rayIntersectsTriangle([.2, .2, 1], [10, 10, 10], # [0, 0, -1],
        [0, 0, 0], [0, 1, 0], [1, 0, 0]
    )

if __name__ == '__main__':
    test6()
