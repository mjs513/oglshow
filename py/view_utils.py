
from scene import BoundingBox
import viewer

try:
    from OpenGL.GL import *
except ImportError:
    _err_exit('ERROR: PyOpenGL not installed properly.')

def draw_bb(bb, do_begin_end = True):
    xmin, ymin, zmin = [bb.xmin, bb.ymin, bb.zmin]
    xmax, ymax, zmax = [bb.xmax, bb.ymax, bb.zmax]

    if do_begin_end:
        glBegin(GL_QUADS)

    # Front Face
    glVertex3f( xmin,  ymin,  zmax)	# Bottom Left Of The Texture and Quad
    glVertex3f( xmax,  ymin,  zmax)	# Bottom Right Of The Texture and Quad
    glVertex3f( xmax,  ymax,  zmax)	# Top Right Of The Texture and Quad
    glVertex3f( xmin,  ymax,  zmax)	# Top Left Of The Texture and Quad

    # Back Face
    glVertex3f( xmin,  ymin,  zmin)	# Bottom Right Of The Texture and Quad
    glVertex3f( xmin,  ymax,  zmin)	# Top Right Of The Texture and Quad
    glVertex3f( xmax,  ymax,  zmin)	# Top Left Of The Texture and Quad
    glVertex3f( xmax,  ymin,  zmin)	# Bottom Left Of The Texture and Quad

    # Top Face
    glVertex3f( xmin,  ymax,  zmin)	# Top Left Of The Texture and Quad
    glVertex3f( xmin,  ymax,  zmax)	# Bottom Left Of The Texture and Quad
    glVertex3f( xmax,  ymax,  zmax)	# Bottom Right Of The Texture and Quad
    glVertex3f( xmax,  ymax,  zmin)	# Top Right Of The Texture and Quad

    # Bottom Face       
    glVertex3f( xmin,  ymin,  zmin)	# Top Right Of The Texture and Quad
    glVertex3f( xmax,  ymin,  zmin)	# Top Left Of The Texture and Quad
    glVertex3f( xmax,  ymin,  zmax)	# Bottom Left Of The Texture and Quad
    glVertex3f( xmin,  ymin,  zmax)	# Bottom Right Of The Texture and Quad

    # Right face
    glVertex3f( xmax,  ymin,  zmin)	# Bottom Right Of The Texture and Quad
    glVertex3f( xmax,  ymax,  zmin)	# Top Right Of The Texture and Quad
    glVertex3f( xmax,  ymax,  zmax)	# Top Left Of The Texture and Quad
    glVertex3f( xmax,  ymin,  zmax)	# Bottom Left Of The Texture and Quad

    # Left Face
    glVertex3f( xmin,  ymin,  zmin)	# Bottom Left Of The Texture and Quad
    glVertex3f( xmin,  ymin,  zmax)	# Bottom Right Of The Texture and Quad
    glVertex3f( xmin,  ymax,  zmax)	# Top Right Of The Texture and Quad
    glVertex3f( xmin,  ymax,  zmin)	# Top Left Of The Texture and Quad

    if do_begin_end:
        glEnd()

def draw_octree(octree):
    def draw_octree_rec(node):
        draw_bb(node.bb, False)
        for child in node.childs:
            draw_octree_rec(child)
    
    with viewer.Wireframe(1.5):
        glBegin(GL_QUADS)
        draw_octree_rec(octree.root)
        glEnd()

    def draw_ray_octree_intersection_rec(node, ray):
        if node.bb.intersect(ray) and not node.childs:
            draw_bb(node.bb, False)
        for child in node.childs:
            draw_ray_octree_intersection_rec(child, ray)

    ray = [ octree.root.bb.min(), octree.root.bb.max() ]
    with viewer.Transparent():
        glBegin(GL_QUADS)
        draw_ray_octree_intersection_rec(octree.root, ray)
        glEnd()

    with viewer.Wireframe(5.0):
        glBegin(GL_LINES)
        glVertex3f( *octree.root.bb.min() )
        glVertex3f( *octree.root.bb.max() )
        glEnd()


