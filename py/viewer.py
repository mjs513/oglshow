#!/usr/bin/python
from __future__ import with_statement

from pdb import set_trace
from math import sqrt, sin, cos, pi, fabs, asin
from time import clock, time
from collections import defaultdict

from utils import _err_exit, notYetImplemented, benchmark
from log import logger, quiet
from math_utils import add_quat, quaternion_to_matrix, multiply_point_by_matrix, common_quaternion_from_angles, sub, add, norm, distance, Trackball, vcross, vnorm, add_quat_wiki

import sys
try:
    sys.path.insert(0, 'cpython/build/lib.macosx-10.5-i386-2.5')
    from cobj import setup, projall, gethits
except ImportError:
    pass
from picking import do_highlight, do_highlight_C, do_highlight_octree
from grid import Grid
from octree import Octree
from view_utils import draw_bb, draw_octree

import numpy as Numeric

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *

    from OpenGL.GL.EXT.bgra import GL_BGRA_EXT as GL_BGRA
    from OpenGL.GL.ARB.vertex_buffer_object import glInitVertexBufferObjectARB, glGenBuffersARB
    from OpenGL.GL.ARB.vertex_buffer_object import glBindBufferARB, glBufferDataARB

except ImportError:
    _err_exit('ERROR: PyOpenGL not installed properly.')

class Transparent(object):
    def __init__(self): pass
    def __enter__(self):
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    def __exit__(self, ty, val, tb):
        glDisable(GL_BLEND)
        return False

class Wireframe(object):
    def __init__(self, width = None, color = None):
        self.line_width = 3.0
        if width is not None:
            self.line_width = width

        self.color = [1.0, 1.0, 1.0]
        if color is not None:
            self.color = color

    def __enter__(self):
        # color = [0.10, 0.10, 0.10]
        # glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, color)
        # glColor3f(*color)

        glPushAttrib( GL_ALL_ATTRIB_BITS )

        # Enable polygon offsets, and offset filled polygons 
        # forward by 2.5
        glEnable( GL_POLYGON_OFFSET_FILL )
        glPolygonOffset( -2.5, -2.5 )

        # Set the render mode to be line rendering with a 
        # thick line width
        glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
        glLineWidth( self.line_width )

        # Set the colour to be white
        glColor3f( *self.color )

    def __exit__(self, ty, val, tb):
        # Pop the state changes off the attribute stack
        # to set things back how they were
        glPopAttrib()
        return False

class OglSdk:
    def __init__(self, _w, _h, _SwapBuffer_cb = None):
        self.w = _w
        self.h = _h
        self.SwapBuffer_cb = _SwapBuffer_cb

        self.mouse_start = [0,0]
        self.button = False
        self.motion = False

        self.fps_counter = 0
        self.timer = time()
        self.fps = 'Unknown'

        self.highlight = False
        self.highlight_cursor = [0, 0]
        self.model = None
        self.proj = None
        self.view = None

        self.show_wireframe = False
        self.octree = False
        self.draw_octree = False
        self.gpu_info = False
        self.normal_dl = None
        self.octree_dl = None

    def load_file(self, fn, verbose = 0, procedural = False):

        # Currently immediate mode is way faster (3x) than Draw array mode
        # cause we have to build the arrays in memory from list objects.
        # We should use module array instead
        # 
        # VBO are 3 to 4 times faster than display list (random test)
        self.do_immediate_mode = False
        # self.do_immediate_mode = False # TEST
        self.use_display_list = False

        self.do_immediate_mode = True
        self.do_vbo = not self.do_immediate_mode
        self.vbo_init = False

        # Style
        self.do_lighting = not self.show_wireframe

        from scene import load
        with benchmark('load from disk'):
            self.scene = load(fn, verbose)
        if not self.scene: return
        self.fn = fn

        if self.use_display_list:
            self.dl = [-1 for i in self.scene.objets]

        # Init quat
        self.trackball = Trackball()

        # highlight setup, for CPython only
        # setup(self.scene.points, self.scene.faces)

        # Grid setup
        if self.octree:
            setup_octree()

        return self.scene

    def setup_octree(self):
        with benchmark('build octree'):
            self.octree = Octree(self.scene)

    def setup_vbo(self):
        glInitVertexBufferObjectARB()
        self.VBO_vertex = int(glGenBuffersARB(1))					# Get A Valid Name
        self.VBO_normal = int(glGenBuffersARB(1))					# Get A Valid Name

        # Load The Data
        sc = self.scene
        self.vbo_array_size = len(sc.faces) * 3
        vertices = Numeric.zeros ( (self.vbo_array_size, 3), 'f')

        if self.do_lighting:
            normals = Numeric.zeros ( (self.vbo_array_size, 3), 'f')
            if not sc.normals:
                print 'compute normals'
                from geom_ops import compute_normals
                sc.normals, sc.faces_normals = compute_normals(sc)

        i = 0
        for j in xrange(len(sc.faces)):
            t = sc.faces[j]
            p1 = sc.points[t[0]]
            p2 = sc.points[t[1]]
            p3 = sc.points[t[2]]

            vertices [i, 0] = p1[0]
            vertices [i, 1] = p1[1]
            vertices [i, 2] = p1[2]

            vertices [i+1, 0] = p2[0]
            vertices [i+1, 1] = p2[1]
            vertices [i+1, 2] = p2[2]

            vertices [i+2, 0] = p3[0]
            vertices [i+2, 1] = p3[1]
            vertices [i+2, 2] = p3[2]

            # print p1, p2, p3

            if self.do_lighting:
                n = sc.faces_normals[j]
                n1 = sc.normals[n[0]]
                n2 = sc.normals[n[1]]
                n3 = sc.normals[n[2]]

                normals [i, 0] = n1[0]
                normals [i, 1] = n1[1]
                normals [i, 2] = n1[2]

                normals [i+1, 0] = n2[0]
                normals [i+1, 1] = n2[1]
                normals [i+1, 2] = n2[2]

                normals [i+2, 0] = n3[0]
                normals [i+2, 1] = n3[1]
                normals [i+2, 2] = n3[2]

            i += 3

        glBindBufferARB( GL_ARRAY_BUFFER_ARB, self.VBO_vertex )
        glBufferDataARB( GL_ARRAY_BUFFER_ARB, vertices, GL_STATIC_DRAW_ARB );

        if self.do_lighting:
            glBindBufferARB( GL_ARRAY_BUFFER_ARB, self.VBO_normal )
            glBufferDataARB( GL_ARRAY_BUFFER_ARB, normals, GL_STATIC_DRAW_ARB );

        if self.gpu_info:
            print glGetString (GL_VENDOR)
            print glGetString (GL_RENDERER)
            print glGetString (GL_VERSION)
            Extensions = glGetString (GL_EXTENSIONS)
            for ext in Extensions.split():
                print ext

        return self.VBO_vertex, self.VBO_normal

    def pointer_move(self, m, xstart, ystart, xend, yend):
        if not self.scene: return
        logger.info('pointer_move: %s %d %d %d %d' % (m, xstart, ystart, xend, yend))

        ww = float(self.w)
        wh = float(self.h)

        view = self.scene.views[0]

        if m == 'zoom':
            dx =  xstart - xend;
            dy = ystart - yend;
            rate = dy / wh if fabs(dy) > fabs(dx) else dx / ww

            #self.scene.views[0].focal *= 1.0 - rate
            view.focal *= 1.0 - rate

        elif m == 'pan':
            prevX = (2.0 * xstart - ww) / ww
            prevY = (2.0 * ystart - wh) / wh
            newX = (2.0 * xend - ww) / ww
            newY = (2.0 * yend - wh) / wh

            window_ratio = ww / wh

            # (from Antoine) je met au milieu de la distance oeil,cible en
            # translate les objets + proches bougeront + vite et les +
            # lointains moins vite 

            DEFAULT_ZOOM = 32.0
            k = self.scene.bb.sphere_beam()

            view.recenterX += -k*(view.focal/DEFAULT_ZOOM) * window_ratio * (prevX - newX);
            view.recenterY +=  k*(view.focal/DEFAULT_ZOOM) * (prevY - newY);

        elif m == 'rotate':

            spin_quat = self.trackball.update(xstart, ystart, xend, yend, ww, wh)
            view.quat = add_quat(spin_quat, view.quat)
            logger.info('quat from trackball %s' % str(view.quat))

    def draw_bg(self):
        glDisable(GL_DEPTH_TEST)
    
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_LIGHTING)

        glBegin(GL_QUADS)
        glColor3ub(24, 26, 28) # Bottom / Blue
        glVertex2f(-1.0,-1.0)
        glVertex2f(1.0,-1.0)
        
        glColor3ub(126, 145, 165) # Top / Red
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)

    def reshape(self, w, h):
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h

    def render(self):
        if self.w == 0 or self.h == 0: 
            return

        if self.do_vbo and not self.vbo_init:
            with benchmark('setup vbo'):
                self.setup_vbo()
            self.vbo_init = True

        logger.info(' === render  === ')

        if not self.scene: 
            #glutSwapBuffers() GLUT
            if self.SwapBuffer_cb:
                self.SwapBuffer_cb()
            return

        # Some OpenGL init
        glEnable(GL_MULTISAMPLE_ARB)
        glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)

        bg_color = map(lambda x: x / 255.0, self.scene.bg)
        bg_color += [1.0]
        glClearColor(*bg_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.draw_bg()
        self.set_lights()
        self.set_matrix(self.scene.views[0])

        # wireframe only is good for debugging, especially
        # when your triangle are just one line: copy/paste error
        # -> and you are trying to draw the triangle A,A,C (instead of A,B,C)
        # using points rendering might another good option
        if self.show_wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
        else:
            glPolygonMode(GL_BACK,GL_FILL)
            glPolygonMode(GL_FRONT,GL_FILL)

        # Render
        self.init_context()
        # with Transparent():
        #     diffus = self.scene.diffus
        #     # We store color in [0,255] interval
        #     diffus = map(lambda x: x / 255.0, diffus)
        #     color = diffus + [0.5]
        #     glColor4f(*color)
        #     self.render_obj()
        self.render_obj()

        if self.show_wireframe:
            with Wireframe(3.0):
                self.render_obj()

        if self.highlight:
            if self.highlight_implementation == "Python":
                do_highlight(self.highlight_cursor, self.scene.faces, self.scene.points)
            elif self.highlight_implementation == "CPython":
                do_highlight_C(self.highlight_cursor, self.scene.faces, self.scene.points)
            elif self.highlight_implementation == "octree":
                do_highlight_octree(self.octree, self.highlight_cursor, self.scene.faces, self.scene.points, self.scene.views[0])

        if self.draw_octree:
            if self.octree_dl is not None:
                glCallList(self.octree_dl)
            else:
                self.octree_dl = glGenLists(1)
                glNewList(self.octree_dl, GL_COMPILE)

                # with viewer.Wireframe('foo'):
                draw_octree(self.octree)

                glEndList()
                glCallList(self.octree_dl)

            if False:
                draw_bb(self.scene.bb)
                for bb in self.scene.bb.split():
                    draw_bb(bb)

        glFlush()
        if self.SwapBuffer_cb:
            self.SwapBuffer_cb()
        #glutSwapBuffers() GLUT

        self.print_fps()

    def print_fps(self):
        ''' Frame per seconds measurement. Displayed on the terminal
        FIXME: display on screen
        ./glut_viewer.py -i test/data/bunny.obj 2>&1 | grep fps
        '''
        max_value = 20 # we measure 20 frames
        self.fps_counter += 1
        if self.fps_counter == max_value:
            t = time()
            f = (t - self.timer) / 20.
            if False:
                logger.warning('frame rendered in %f' % (f))
                logger.warning('fps %f' % (1. / f))
            self.timer = t
            self.fps_counter = 0
            self.fps = '%.2f' % (1. / f)

    def init_context(self):
        diffus   = self.scene.diffus
        specular = self.scene.specular
        ambiant  = self.scene.ambiant
        emis     = self.scene.specular
        shine    = self.scene.shine

        if self.do_lighting: # obj.light_on_off:
            glEnable(GL_LIGHTING)
        else:
            glDisable(GL_LIGHTING)

        # We store color in [0,255] interval
        diffus = map(lambda x: x / 255.0, diffus)
        specular = map(lambda x: x / 255.0, specular)
        ambiant = map(lambda x: x / 255.0, ambiant)
        emis = map(lambda x: x / 255.0, emis)

        glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, shine)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, emis)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)

        # FIXME: Usual Ugly material trick 
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, diffus)

        # Material
        glColor3f(*diffus)

    def render_obj(self):
        logger.info(' === render === ')
        sc = self.scene

        if self.do_vbo:
            glEnableClientState( GL_VERTEX_ARRAY )
            glEnableClientState( GL_NORMAL_ARRAY )

            glBindBufferARB( GL_ARRAY_BUFFER_ARB, self.VBO_vertex )
            glVertexPointer( 3, GL_FLOAT, 0, None )

            if self.do_lighting:
                glBindBufferARB( GL_ARRAY_BUFFER_ARB, self.VBO_normal )
                glNormalPointer( GL_FLOAT, 0, None )

            glDrawArrays( GL_TRIANGLES, 0, self.vbo_array_size )

            glDisableClientState( GL_VERTEX_ARRAY )
            glDisableClientState( GL_NORMAL_ARRAY ) 

        if self.do_immediate_mode:
            glBegin(GL_TRIANGLES)

            # Factorisation might be bad for performances
            def send_point_to_gl(p):
                # Order: texture, normal, points
                if False and p.coord_mapping:
                    glTexCoord2f(*p.coord_mapping)
                if p.normal:
                    glNormal3f(*p.normal)
                glVertex3f(*p)

            for j in xrange(len(sc.faces)):
                t = sc.faces[j]
                p1 = sc.points[t[0]]
                p2 = sc.points[t[1]]
                p3 = sc.points[t[2]]

                n = sc.faces_normals[j]
                n1 = sc.normals[n[0]]
                n2 = sc.normals[n[1]]
                n3 = sc.normals[n[2]]

                glNormal3f(*n1)
                glVertex3f(*p1)
                glNormal3f(*n2)
                glVertex3f(*p2)
                glNormal3f(*n3)
                glVertex3f(*p3)

            glEnd()

        display_normals = False
        if display_normals:
            if self.normal_dl is not None:
                glCallList(self.normal_dl)
            else:
                self.normal_dl = glGenLists(1)
                glNewList(self.normal_dl, GL_COMPILE)

                glBegin(GL_LINES)
                glColor3f(0.0, 0.0, 1.0)

                def draw_normal(p, n):
                    glVertex3fv(p)
                    N = map(lambda x, y: x + y, p, n)
                    glVertex3fv(N)

                for j, t in enumerate(sc.faces):
                    p1 = sc.points[t[0]]
                    p2 = sc.points[t[1]]
                    p3 = sc.points[t[2]]

                    n1 = sc.normals[j][0]
                    n2 = sc.normals[j][1]
                    n3 = sc.normals[j][2]
                    
                    draw_normal(p1, n1)
                    draw_normal(p2, n2)
                    draw_normal(p3, n3)

                glEnd()
                glEndList()
                glCallList(self.normal_dl)

    def set_lights(self):
        self.set_default_light()

    def set_default_light(self):
        default_ambiant = 0.22
        LightDiffuse = [ \
                1.0 - default_ambiant, 1.0 - default_ambiant, 
                1.0 - default_ambiant, 1.0]
        LightAmbiant      = [ 0, 0, 0, 1.0 ];
        LightSpecular     = [ 1.0, 1.0, 1.0, 1.0 ]
        LightAmbiantScene = [ default_ambiant, default_ambiant, default_ambiant, 1.0 ]

        # Needed because when passing light infos : The position is transformed by the
        # modelview matrix when glLight is called (just as if it were a point), and it
        # is stored in eye coordinates.  If the w component of the position is 0.0, the
        # light is treated as a directional source. 
        #
        # Save model view
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glLightModelf(GL_LIGHT_MODEL_TWO_SIDE, 1.0)

        # Facial light - LIGHT 1
        look = [0.,0.,-1.]
        quat = common_quaternion_from_angles(30.,30.,0.)
        v = multiply_point_by_matrix(quaternion_to_matrix(quat), look)
        light0Pos = map(lambda x: x * -1., v) # * -1

        matShine = 60.00
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, matShine)
        glLightfv(GL_LIGHT0, GL_POSITION, light0Pos)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, LightAmbiantScene)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, LightDiffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, LightSpecular)
        glLightfv(GL_LIGHT0, GL_AMBIENT, LightAmbiant)
        glEnable(GL_LIGHT0)

        if True:
            # Opposite light - LIGHT 2
            matShine = 60.00
            light1Pos = [ -0.7, -0.7, -0.7, 0.00 ]
            LightDiffuse = [1.0, 1.0, 1.0, 1.0]

            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, matShine)
            glLightfv(GL_LIGHT1, GL_POSITION, light1Pos)
            glLightfv(GL_LIGHT1, GL_DIFFUSE, LightDiffuse)
            glLightfv(GL_LIGHT1, GL_SPECULAR, LightDiffuse)
            glEnable(GL_LIGHT1)

        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)

        # restore modelview
        glPopMatrix()

    def set_matrix(self, v):
        '''
        To debug this, make sure gluPerspective and gluLookAt have
        the same parameter when given the same mouse events in cpp and in python
        '''

        ############
        # Projection
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity()

        pixel_ratio = self.w / float(self.h)
        zF = v.focal / 30.0

        diam2 = 2.0 * self.scene.bb.sphere_beam()

        look = sub(v.tget, v.eye)
        diam = 0.5 * norm(look)
        recul = 2 * diam

        zNear = 0.01 * recul # 1% du segment de visee oeil-cible
        zFar = recul + diam2

        if pixel_ratio < 1:
            zF /= pixel_ratio

        logger.info('gluPerspective %f %f %f %f' % (zF*30, pixel_ratio, zNear, zFar))
        gluPerspective (zF*30, pixel_ratio, zNear, zFar)
        # For debug: hard-coded values for some models
        #gluPerspective ( 32, 1.34, 27, 54 ) # Gears
        #gluPerspective ( 32, 1.44, 204, 409 ) # spaceship

        ############
        # Model View
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glTranslatef(v.recenterX, v.recenterY, 0.0)

        # Take care of the eye
        rotation_matrix = quaternion_to_matrix(v.quat)
        new_look = [0, 0, recul] # LOL name
        v.eye = multiply_point_by_matrix(rotation_matrix, new_look)
        v.eye = add(v.eye, self.scene.bb.center())

        # Vector UP (Y)
        vup_t = multiply_point_by_matrix(rotation_matrix, [0.0, 1.0, 0.0])
        logger.info('gluLookAt eye  %s' % str(v.eye))
        logger.info('gluLookAt tget %s' % str(v.tget))
        logger.info('gluLookAt vup  %s' % str(vup_t))

        gluLookAt (	v.eye[0], v.eye[1], v.eye[2],
                    v.tget[0], v.tget[1], v.tget[2],
                    vup_t[0], vup_t[1], vup_t[2] )

    def swap_buffer(self):
        if self.SwapBuffer_cb:
            self.SwapBuffer_cb()

