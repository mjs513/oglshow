from __future__ import with_statement

from os.path import join
from scene import Scene, load, ArgsOptions
from pdb import set_trace

from utils import _err_exit
import viewer 
try:
    from OpenGL.GL import *
except ImportError:
    _err_exit('ERROR: PyOpenGL not installed properly.')

class Grid():
    def __init__(self, sc):
        self.sc = sc

        bb = sc.compute_bb()
        self.bb = bb
        print bb

        # 10 by 10 by 10
        # Base size in Megs for different grid sizes ... 
        # will be much bigger
        # >>> 200 ** 3 / 1000000
        # 8
        # >>> 500 ** 3 / 1000000
        # 125
        
        size = 3
        x = [ None for i in xrange(size) ]
        y = [ x    for i in xrange(size) ]
        z = [ y    for i in xrange(size) ]
        grid = z

        X = bb.xmax - bb.xmin
        Y = bb.ymax - bb.ymin
        Z = bb.zmax - bb.zmin

        self.X = X
        self.Y = Y
        self.Z = Z

        for t in sc.faces:
            p1 = sc.points[t[0]]
            p2 = sc.points[t[1]]
            p3 = sc.points[t[2]]

            for p in [p1, p2, p3]:
                def get_index(init, size, width, axis, point):
                    s = init
                    for i in xrange(size):
                        s += width / size
                        if s > point[axis]:
                            return i
                    return int(size - 1)

                i = get_index(bb.xmin, size, X, 0, p)
                j = get_index(bb.ymin, size, Y, 1, p)
                k = get_index(bb.zmin, size, Z, 2, p)

                if any(q is None for q in [i, j, k]):
                    print 'pb with grid ...'
                    set_trace()

                if grid[i][j][k] is not None:
                    grid[i][j][k].append( t )
                else:
                    grid[i][j][k] = [t]

        #print grid

    def draw(self):
        print 'draw grid'

        bb = self.bb
        xmin, ymin, zmin = [bb.xmin, bb.ymin, bb.zmin]
        xmax, ymax, zmax = [bb.xmax, bb.ymax, bb.zmax]

        with viewer.wireframe('foo'):
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

            glEnd()

def main():
    sc = load( join('data', 'gears.obj') )
    g = Grid(sc)

if __name__ == '__main__':
    main()
    
