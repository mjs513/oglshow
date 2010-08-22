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
        triangle_normals = len(sc.faces) * [ [.0, .0, .0] ]

        def hash(p):
            return .11234 * p[0] + .35678 * p[1] + .67257 * p[2]

        from collections import defaultdict
        pt_table = defaultdict(list)

        for i, t in enumerate(sc.faces):
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
        scene.normals, scene.faces_normals = compute_normals(scene)
    scene.write(sys.argv[2])

def test6():
    from math_utils import rayIntersectsTriangle
    print rayIntersectsTriangle([.2, .2, 1], [10, 10, 10], # [0, 0, -1],
        [0, 0, 0], [0, 1, 0], [1, 0, 0]
    )

def test7():
    with open(sys.argv[1]) as f:
        points = []
        faces = []
        for i, line in enumerate(f):
            x1, y1, z1, x2, y2, z2, x3, y3, z3 = map(float, line.split())
            points.append( (x1, y1, z1) )
            points.append( (x2, y2, z2) )
            points.append( (x3, y3, z3) )
            faces.append( (3*i, 3*i + 1, 3*i +2) )

        from scene import Scene
        sc = Scene()
        sc.points = points
        sc.faces = faces
        sc.write('/tmp/out.obj')

def read_geom(input):
    cmd = "awk 'BEGIN { quad = 0; vn = 0 } /^v / { v++ } /^vn / { vn++ } /^f / { f++; } /^f / && NF == 5 { quad++ } END { print v,vn,f,quad }' "
    cmd += fn
    out = popen(cmd).read()
    nb_points, nb_normals, nb_faces, quad = map(int, out.split())
    print nb_points, nb_faces, nb_normals, quad

    points = range(nb_points)
    normals = range(nb_normals)
    size = nb_faces * 2 if quad else nb_faces
    faces = range(size)
    faces_normals = range(size)

    vn, v, f = 0, 0, 0

    for line in open(input):
        line = line.strip()
        if line.startswith('#'): continue

        tokens = line.split()
        if line.startswith('v '):
            points[v] = map(float, tokens[1:])
            v += 1

        elif line.startswith('f'):
            positions = []
            normal_positions = []
            for vert in tokens[1:]:
                components = vert.split('/')
                positions.append( int(components[0]) - 1 )
                if len(components) == 3:
                    normal_positions.append( int(components[2]) - 1 )
                    
            # triangle ?
            if len(positions) == 3:
                faces[f] = positions
                if normal_positions:
                    faces_normals[f] = normal_positions
                f += 1

            else: # let's say it's a quad
                faces.append(positions[0:3])
                faces.append(positions[2:] + [positions[0]])
                if normal_positions:
                    faces_normals.append(normal_positions[0:3])
                    faces_normals.append(normal_positions[2:] + [normal_positions[0]])

        elif line.startswith('vn'):
            normals[vn] = map(float, tokens[1:])
            vn += 1

    return points, faces, normals, faces_normals


if __name__ == '__main__':
    test2()
