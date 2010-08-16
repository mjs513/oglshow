#!/usr/bin/env python
import sys

from viewer import OglSdk
from scene import load
from math_utils import vcross, vnorm, sub
from utils import _err_exit, notYetImplemented, benchmark

def compute_normals(sc):
    out = []
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

    i = 0
    normals = []
    faces_normals = []
    for t in sc.faces:
        p1 = sc.points[t[0]]
        p2 = sc.points[t[1]]
        p3 = sc.points[t[2]]

        face_normals = []
        for point in [p1, p2, p3]:
            # we assume no collisions in the hash
            value = pt_table[hash(point)]
            point_index = value[0][2]
            first_point = value[0][1]

            # compute the normal of each triangles around 
            # TODO should be done just once for each triangle in pre-process
            neighbors_normals = []

            for t_index, p, _ in value:
                assert p == first_point
                neighbors_normals.append(triangle_normals[t_index])
            
            N = (
                sum(n[0] for n in neighbors_normals) / len(neighbors_normals),
                sum(n[1] for n in neighbors_normals) / len(neighbors_normals),
                sum(n[2] for n in neighbors_normals) / len(neighbors_normals)
            )

            # normalize normal
            N = vnorm(N)

            # print N
            normals.append(N)

        faces_normals.append( (3*i, 3*i+1, 3*i+2) )
        i += 1

    return normals, faces_normals
