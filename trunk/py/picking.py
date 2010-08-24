from __future__ import with_statement

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    _err_exit('ERROR: PyOpenGL not installed properly.')

from pdb import set_trace
import sys
sys.path.insert(0, 'cpython/build/lib.macosx-10.5-i386-2.5')
from cobj import setup, projall, gethits

from math_utils import vsub
from utils import benchmark
import viewer

self_model = None
self_proj = None
self_view = None
image_points = None

class Point2D():
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

def display_hits(hits, points):
    if hits:
        print 'Hit'
        hits.sort()
        hit = hits[0]
        t = hit[1]

        p1 = points[t[0]]
        p2 = points[t[1]]
        p3 = points[t[2]]

        with viewer.Wireframe(2.0): # FIXME: 'white'):
            glBegin(GL_TRIANGLES)
            glVertex3f(*p1)
            glVertex3f(*p2)
            glVertex3f(*p3)
            glEnd()
        with in_red():
            glBegin(GL_TRIANGLES)
            glVertex3f(*p1)
            glVertex3f(*p2)
            glVertex3f(*p3)
            glEnd()
    else:
        print 'no hit'

class in_red(object):
    def __init__(self): pass
    def __enter__(self):
        glPushAttrib( GL_ALL_ATTRIB_BITS )

        glPolygonMode(GL_BACK,GL_FILL)
        glPolygonMode(GL_FRONT,GL_FILL)

        glEnable( GL_POLYGON_OFFSET_FILL )
        glPolygonOffset( -2.5, -2.5 )

        glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)

        # Set the colour to be red
        glColor3f( 1.0, 0.0, 0.0 )

    def __exit__(self, ty, val, tb):
        # Pop the state changes off the attribute stack
        # to set things back how they were
        glPopAttrib()
        return False

def do_highlight(highlight_cursor, faces, points):
    global self_model, self_proj, self_view, image_points

    # the gluProject helper retrieve those for us 
    # but calling this once is a good time save speedup 
    model = glGetDoublev( GL_MODELVIEW_MATRIX )
    proj = glGetDoublev( GL_PROJECTION_MATRIX )
    view = glGetIntegerv( GL_VIEWPORT )

    # same camera ?
    def same_float_array(X, Y):
        Z = X - Y
        for i in Z:
            for j in i:
                if abs(j) > 0.00001:
                    return False
        return True

    V = view == self_view
    if not isinstance(V, bool):
        V = V.all()
        
    same_camera = V and \
        same_float_array(model, self_model) and \
        same_float_array(proj, self_proj)

    self_model = model
    self_proj = proj
    self_view = view

    def cross_product_2d(U, V):
        return U.x * V.y - U.y * V.x

    def cross_product_2d_list(U, V):
        # print U[0], V[1], U[1], V[0]
        return U[0] * V[1] - U[1] * V[0]

    class Vector():
        __slots__ = ('x', 'y')
        def __init__(self, A, B):
            self.x = B.x - A.x
            self.y = B.y - A.y

    class Triangle():
        __slots__ = ('A', 'B', 'C')
        def __init__(self, A, B, C):
            self.A = A
            self.B = B
            self.C = C

        def is_inside(self, P, verbose = False):
            b1 = cross_product_2d( Vector(P,self.A), Vector(P,self.B) ) >= 0
            b2 = cross_product_2d( Vector(P,self.B), Vector(P,self.C) ) >= 0
            b3 = cross_product_2d( Vector(P,self.C), Vector(P,self.A) ) >= 0
            return b1 == b2 == b3

    cursor = Point2D(*highlight_cursor)
    hits = []

    if not same_camera:
        with benchmark('glu'):
            image_points = []

            for p in points:
                x, y, z = gluProject(p[0], p[1], p[2], model, proj, view)
                image_points.append( (x,y,z) )
                # print view, x, y, z

    with benchmark('python'):
        for t in faces:
            x1, y1, z1 = image_points[t[0]]
            x2, y2, z2 = image_points[t[1]]
            x3, y3, z3 = image_points[t[2]]

            if False:
                P1 = Point2D(x1, y1)
                P2 = Point2D(x2, y2)
                P3 = Point2D(x3, y3)
                t_image = Triangle(P1, P2, P3)
                inside = t_image.is_inside(cursor)
            else:
                # 2 to 3 times faster if we dont build Point and Triangle objects
                x, y = cursor.x, cursor.y
                # print x, y
                b1 = cross_product_2d_list( (x - x1, y - y1), (x - x2, y - y2) ) >= 0
                b2 = cross_product_2d_list( (x - x2, y - y2), (x - x3, y - y3) ) >= 0
                b3 = cross_product_2d_list( (x - x3, y - y3), (x - x1, y - y1) ) >= 0
                inside = b1 == b2 == b3

            if inside:
                print t
                hits.append( (max(z1, z2, z3), t) )

    display_hits(hits, points)
        
def do_highlight_C(highlight_cursor, faces, points):
    global self_model, self_proj, self_view

    # the gluProject helper retrieve those for us 
    # but calling this once is a good time save speedup 
    model = glGetDoublev( GL_MODELVIEW_MATRIX )
    proj = glGetDoublev( GL_PROJECTION_MATRIX )
    view = glGetIntegerv( GL_VIEWPORT )

    # same camera ?
    def same_float_array(X, Y):
        Z = X - Y
        for i in Z:
            for j in i:
                if abs(j) > 0.00001:
                    return False
        return True

    V = view == self_view
    if not isinstance(V, bool):
        V = V.all()
        
    same_camera = V and \
        same_float_array(model, self_model) and \
        same_float_array(proj, self_proj)

    self_model = model
    self_proj = proj
    self_view = view

    cursor = Point2D(*highlight_cursor)

    if not same_camera:
        with benchmark('glu'):

            model_as_list = model[0].tolist() + \
                model[1].tolist() + \
                model[2].tolist() + \
                model[3].tolist() 
            proj_as_list = proj[0].tolist() + \
                proj[1].tolist() + \
                proj[2].tolist() + \
                proj[3].tolist()
            view_as_list = view.tolist()

            projall(model_as_list, proj_as_list, view_as_list)

    with benchmark('python'):
        hits = gethits(cursor.x, cursor.y)

        display_hits(hits, points)
        return True

def do_highlight_octree(octree, mouse, faces, points, sc_view):
    model = glGetDoublev( GL_MODELVIEW_MATRIX )
    proj = glGetDoublev( GL_PROJECTION_MATRIX )
    view = glGetIntegerv( GL_VIEWPORT )

    tget = gluUnProject(mouse[0], mouse[1], 0, model, proj, view)

    segment = (sc_view.eye, tget)
    hit = octree.intersect(segment)

    if hit:
        print hit
        hit = hit[0]
        with in_red():
            glBegin(GL_TRIANGLES)
            glVertex3fv(points[hit[0]])
            glVertex3fv(points[hit[1]])
            glVertex3fv(points[hit[2]])
            glEnd()
    else:
        print 'no hit'
