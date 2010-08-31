#!/usr/bin/env python
from __future__ import with_statement

from pdb import set_trace # Comment it to remove winpdb warning
# import vimpdb; vimpdb.set_trace()

from optparse import OptionParser
from os.path import join, exists, splitext
from os import getpid, getenv, remove, stat
from stat import ST_SIZE
from time import clock
from copy import deepcopy
from platform import uname
from sys import exit
import logging
from sys import maxint

from log import logger, quiet
from utils import get_username, flatten, benchmark
from math_utils import apply_matrix_on_point, common_quaternion_from_angles
from math_utils import multiply_point_by_matrix as point_by_matrix
from math_utils import quaternion_to_matrix
from math_utils import distance, add
from math_utils import rayIntersectsQuad
from math_utils import build_ray

class BoundingBox:
    def __init__(self, A=None, B=None):
        # python print 'inf' for such a number. 
        # Dont know how to specify MAX_FLOAT, use maxint
        if A is None and B is None:
            infinity = maxint

            self.xmin = infinity
            self.ymin = infinity
            self.zmin = infinity

            self.xmax = -1 * infinity
            self.ymax = -1 * infinity
            self.zmax = -1 * infinity
        else:
            self.xmin = A[0]
            self.ymin = A[1]
            self.zmin = A[2]

            self.xmax = B[0]
            self.ymax = B[1]
            self.zmax = B[2]

    def add_points(self, L):
        ''' L is a list of points - Strangely the copy paste method is
        faster :) It takes more memory thought, it basically double the
        number of points Having to call a function (min or max)
        Performances: A > B > C > D
        See commit before firt pylint lifting to see those other methods
        that were removed to have a cleaner code
        '''
        # Calling a function kills performances. So we code our own
        # min, max. But looping in python is slow as opposed to looping
        # in C

        for x, y, z in L:
            self.xmin = x if x < self.xmin else self.xmin
            self.ymin = y if y < self.ymin else self.ymin
            self.zmin = z if z < self.zmin else self.zmin

            self.xmax = x if x > self.xmax else self.xmax
            self.ymax = y if y > self.ymax else self.ymax
            self.zmax = z if z > self.zmax else self.zmax

    def add(self, other):
        ''' FIXME: Learn to do that the pythonic way 
        ie: Adding a + operator
        '''
        self.xmin = min(self.xmin, other.xmin)
        self.ymin = min(self.ymin, other.ymin)
        self.zmin = min(self.zmin, other.zmin)

        self.xmax = max(self.xmax, other.xmax)
        self.ymax = max(self.ymax, other.ymax)
        self.zmax = max(self.zmax, other.zmax)

    def sphere_beam(self):
        return distance([self.xmax, self.ymax, self.zmax],
                [self.xmin, self.ymin, self.zmin]) / 2.0

    def center(self):
        return [(self.xmin + self.xmax) / 2,
                (self.ymin + self.ymax) / 2,
                (self.zmin + self.zmax) / 2 ]

    def min(self): return [self.xmin, self.ymin, self.zmin]
    def max(self): return [self.xmax, self.ymax, self.zmax]

    def is_inside(self, V):
        return self.xmin <= V[0] <= self.xmax and \
               self.ymin <= V[1] <= self.ymax and \
               self.zmin <= V[2] <= self.zmax

    def split(self):
        xmin = self.xmin
        ymin = self.ymin
        zmin = self.zmin

        xmax = self.xmax
        ymax = self.ymax
        zmax = self.zmax

        xcen, ycen, zcen = self.center()

        yield BoundingBox( [xmin, ymin, zmin], [xcen, ycen, zcen] )
        yield BoundingBox( [xmin, ycen, zmin], [xcen, ymax, zcen] )
        yield BoundingBox( [xcen, ymin, zmin], [xmax, ycen, zcen] )
        yield BoundingBox( [xcen, ycen, zmin], [xmax, ymax, zcen] )

        yield BoundingBox( [xmin, ymin, zcen], [xcen, ycen, zmax] )
        yield BoundingBox( [xmin, ycen, zcen], [xcen, ymax, zmax] )
        yield BoundingBox( [xcen, ymin, zcen], [xmax, ycen, zmax] )
        yield BoundingBox( [xcen, ycen, zcen], [xmax, ymax, zmax] )

    def intersect(self, ray):
        xmin, ymin, zmin = [self.xmin, self.ymin, self.zmin]
        xmax, ymax, zmax = [self.xmax, self.ymax, self.zmax]
        front, back, top, bottom, right, left = [[] for i in range(6)]

        # Front Face
        front.append(( xmin,  ymin,  zmax))
        front.append(( xmax,  ymin,  zmax))	
        front.append(( xmax,  ymax,  zmax))
        front.append(( xmin,  ymax,  zmax))

        # Back Face
        back.append(( xmin,  ymin,  zmin))
        back.append(( xmin,  ymax,  zmin))
        back.append(( xmax,  ymax,  zmin))
        back.append(( xmax,  ymin,  zmin))

        # Top Face
        top.append(( xmin,  ymax,  zmin))
        top.append(( xmin,  ymax,  zmax))
        top.append(( xmax,  ymax,  zmax))
        top.append(( xmax,  ymax,  zmin))

        # Bottom Face       
        bottom.append(( xmin,  ymin,  zmin))
        bottom.append(( xmax,  ymin,  zmin))
        bottom.append(( xmax,  ymin,  zmax))
        bottom.append(( xmin,  ymin,  zmax))

        # Right face
        right.append(( xmax,  ymin,  zmin))
        right.append(( xmax,  ymax,  zmin))
        right.append(( xmax,  ymax,  zmax))
        right.append(( xmax,  ymin,  zmax))

        # Left Face
        left.append(( xmin,  ymin,  zmin))
        left.append(( xmin,  ymin,  zmax))
        left.append(( xmin,  ymax,  zmax))
        left.append(( xmin,  ymax,  zmin))

        return rayIntersectsQuad(ray, front) or \
               rayIntersectsQuad(ray, back)  or \
               rayIntersectsQuad(ray, top)   or \
               rayIntersectsQuad(ray, bottom) or \
               rayIntersectsQuad(ray, right) or \
               rayIntersectsQuad(ray, left) 
    
    def intersect_triangle(self, face, verts):
        return self.intersect( build_ray( (verts[face[0]], verts[face[1]]) ) ) or \
               self.intersect( build_ray( (verts[face[1]], verts[face[2]]) ) ) or \
               self.intersect( build_ray( (verts[face[2]], verts[face[0]]) ) )

    def __str__(self):
        s = '\nxmin %f xmax %f\n' % (self.xmin, self.xmax)
        s +=  'ymin %f ymax %f\n' % (self.ymin, self.ymax)
        s +=  'zmin %f zmax %f\n' % (self.zmin, self.zmax)
        return s

class View:
    def __init__(self):
        self.recenterX = 0.0
        self.recenterY = 0.0
        self.focal = 0.0
        self.quat = [0.0, 0.0, 0.0, 0.0]
        self.eye = [0.0, 0.0, 0.0]
        self.tget = [0.0, 0.0, 0.0]
        self.comment = ''
        self.name = ''
        self.roll = 0.0

    def reset(self, _bb):
        self.recenterX = 0.0
        self.recenterY = 0.0
        self.focal = 32.0
        self.quat = common_quaternion_from_angles(180, 45+22.5, 0 )
        self.quat = [-0.23, 0.40, 0.090, 0.88]

        recul = 1.5 * _bb.sphere_beam()
        if False: # try to mimic cpp but that does not work
            look = [0.0, 0.0, recul]
            self.eye = point_by_matrix(quaternion_to_matrix(self.quat), look)
            self.tget = look

        # Using sub(_bb.min(), [recul, recul, recul]) has the same effects
        self.eye = add([recul, recul, recul], _bb.max())
        self.tget = _bb.center()

    def empty(self):
        zero = 3 * [0.0]
        return self.eye == zero and self.tget == zero \
                and self.focal == 0.0 and self.roll == 0.0 \
                and self.recenterX == 0.0 and self.recenterY == 0.0

    def __str__(self):
        s =  '\nQuat %s\n' % str(self.quat)
        s += 'Eye %s\n' % str(self.eye)
        s += 'Target %s\n' % str(self.tget)
        s += 'Focal %f\n' % self.focal
        s += 'Roll %f\n' % self.roll
        s += 'recenterX %f\n' % self.recenterX
        s += 'recenterY %f\n' % self.recenterY
        return s

class Scene:
    def __init__(self):
        # metadatas
        self.fn = None
        self.filesize = 0

        # geom
        self.points = []
        self.faces = []
        self.normals = []
        self.faces_normals = []

        # material
        self.diffus = 3 * [0]
        self.diffus = [51, 51, 255]
        
        self.specular = 3 * [0]
        self.ambiant = 3 * [0]
        self.emis = 3 * [0]
        self.shine = 0.0

        # rendering
        self.views = []
        self.bg = 3 * [0]

    def read(self, fn):
        self.fn = fn
        self.filesize = stat(fn)[ST_SIZE]

        def read_geom(input):
            points = []
            faces = []
            normals = []
            faces_normals = []

            for line in open(input):
                line = line.strip()
                if line.startswith('#'): continue

                tokens = line.split()
                if line.startswith('v '):
                    points.append( map(float, tokens[1:]) ) 
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
                        faces.append(positions)
                        if normal_positions:
                            faces_normals.append(normal_positions)
                    else: # let's say it's a quad
                        faces.append(positions[0:3])
                        faces.append(positions[2:] + [positions[0]])
                        if normal_positions:
                            faces_normals.append(normal_positions[0:3])
                            faces_normals.append(normal_positions[2:] + [normal_positions[0]])

                elif line.startswith('vn'):
                    normals.append( map(float, tokens[1:]) )

            return points, faces, normals, faces_normals

        def read_geom_C(input):
            import cobj
            return cobj.read(input)

        try:
            import caca
            self.points, self.faces, self.normals, self.faces_normals = \
                read_geom_C(fn)
        except ImportError:
            self.points, self.faces, self.normals, self.faces_normals = \
                read_geom(fn)

    def write(self, fn, comp_type = None):
        f = open(fn, 'w')
        for v in self.points:
            f.write('v %f %f %f\n' % (v[0], v[1], v[2]))

        if not self.normals:
            for t in self.faces:
                f.write('f %d %d %d\n' % (t[0]+1, t[1]+1, t[2]+1))
        else:
            for n in self.normals:
                f.write('vn %f %f %f\n' % (n[0]+1, n[1]+1, n[2]+1))

            for i in xrange(len(self.faces)):
                t = self.faces[i]
                n = self.faces_normals[i]
                f.write('f %d//%d %d//%d %d//%d\n' % \
                    (t[0]+1, n[0]+1, t[1]+1, n[1]+1, t[2]+1, n[2]+1))

        f.close()

    def compute_bb(self):
        bb = BoundingBox()
        bb.add_points(self.points)
        return bb

    def get_infos(self):
        nb_pts = len(self.points)
        nb_triangles = len(self.faces)
        return nb_pts, nb_triangles

    def __str__(self):
        s =  'File name %s\n' % self.fn
        s += 'File size %d\n' % self.filesize
        s += '\n'
        s += 'nb points %d\n' % len(self.points)
        s += 'nb faces %d\n' % len(self.faces)
        s += 'nb normals %d\n' % len(self.normals)
        s += 'nb faces_normals %d\n' % len(self.faces_normals)

        return s

def load(fn, verbose = 0):
    ''' load an obj file and return a scene '''
    verbosity = {
            0: logging.WARNING, # FIXME: what should we do with logging.ERROR ?
            1: logging.INFO,
            2: logging.DEBUG,
            }
    logger.setLevel(verbosity[verbose])

    sc = Scene()
    sc.read(fn)
    sc.bb = sc.compute_bb()

    if sc.views == []:
        logger.info('No views in file, creating one dummy view')
        sc.views = [View()]

    v = sc.views[0]
    logger.info(v.__str__())
    if v.empty():
        logger.info('Recompute first view')
        v.reset(sc.bb)

    logger.info(sc.__str__())
    return sc

class ArgsOptions(object):

    def __init__(self):
        # parse args
        usage = "usage: python %prog <options>"
        parser = OptionParser(usage=usage)

        parser.add_option("-i", "--input-file", dest="fn",
                          help="The file to read [%default]")
        parser.add_option("-v", "--verbose", dest="verbose", 
                          help="Enable logging")
        parser.add_option("-p", "--pid", dest="pid", action="store_true",
                          help="Print pid")
        parser.add_option("-b", "--big", dest="procedural", action="store_true",
                          help="Create a big file with lots of polygons")
        parser.add_option("-n", "--net", dest="net", action="store_true",
                          help="Browse list of file to open from a PDF server")
        fn = 'bunny.obj'
        fn = 'teddy.obj'
        parser.set_defaults(
            fn = join('test', 'data', fn), # 
            verbose = 0,
            pid = False,
            procedural = False)
        
        self.options, args = parser.parse_args()

        if self.options.pid:
            print 'copy paste to kill me'
            print 'kill -9 %d' % getpid()
            raw_input()
        if not self.options.verbose:
            quiet()
        else:
            self.options.verbose = int(self.options.verbose)

def main():
    ao = ArgsOptions()
    options = [ao.options.fn,
               ao.options.verbose]

    with benchmark('load'):
        sc = load(*options)
        print sc

if __name__ == '__main__':
    main()

# From a python interpreter:
'''
from scene import Scene
scene = Scene()
scene.read('/path/to/foo.obj')
'''
