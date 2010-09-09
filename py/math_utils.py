from math import sqrt, sin, cos, pi, fabs, asin
from pdb import set_trace
from copy import deepcopy

from log import logger, quiet

# Math helpers
def quaternion_to_matrix(q):
    qx, qy, qz, qw = q
    return [
            [1 - 2*qy**2 - 2*qz**2, 
                2*qx*qy - 2*qz*qw,
                2*qx*qz + 2*qy*qw],
            [2*qx*qy + 2*qz*qw,	
                1 - 2*qx**2 - 2*qz**2, 
                2*qy*qz - 2*qx*qw],
            [2*qx*qz - 2*qy*qw,
                2*qy*qz + 2*qx*qw,
                1 - 2*qx**2 - 2*qy**2]
    ]

def multiply_point_by_matrix(m, p):
    return [m[0][0]*p[0] + m[0][1]*p[1] + m[0][2]*p[2], 
			m[1][0]*p[0] + m[1][1]*p[1] + m[1][2]*p[2],
			m[2][0]*p[0] + m[2][1]*p[1] + m[2][2]*p[2]]

def apply_matrix_on_point(m, p):
    x, y, z = p
    return [ x*m[0] + y*m[4] + z*m[8]  + m[12],
			 x*m[1] + y*m[5] + z*m[9]  + m[13],
			 x*m[2] + y*m[6] + z*m[10] + m[14]]

def common_quaternion_from_angles(fYaw, fPitch, fRoll):
    ''' from geom_base.cpp '''
    quat = range(4)
    degre2rad = pi / 180.0 # FIXME use math.radians instead

    fYaw *= degre2rad
    fPitch *= degre2rad
    fRoll *= degre2rad

    fSinYaw   = sin( fYaw*0.5 )
    fSinPitch = sin( fPitch*0.5 )
    fSinRoll  = sin( fRoll*0.5 )
    fCosYaw   = cos( fYaw*0.5 )
    fCosPitch = cos( fPitch*0.5 )
    fCosRoll  = cos( fRoll*0.5 )

    quat[0] = fSinRoll * fCosPitch * fCosYaw
    quat[1] = fCosRoll * fSinPitch * fCosYaw
    quat[2] = fCosRoll * fCosPitch * fSinYaw
    quat[3] = fCosRoll * fCosPitch * fCosYaw

    quat[0] -= fCosRoll * fSinPitch * fSinYaw
    quat[1] += fSinRoll * fCosPitch * fSinYaw
    quat[2] -= fSinRoll * fSinPitch * fCosYaw
    quat[3] += fSinRoll * fSinPitch * fSinYaw
    return quat

def sub(x, y):
    return map(lambda a, b: a-b, x, y)

def add(x, y):
    return map(lambda a, b: a+b, x, y)

def norm(v):
    return sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def distance(A, B):
    return norm(sub(A,B))

class Trackball:
    '''A trackball object.  This is deformed trackball which is a hyperbolic
       sheet of rotation away from the center. This particular function was chosen
       after trying out several variations.  The current transformation matrix
       can be retrieved using the "matrix" attribute.'''


    def __init__(self, size = 0.8, scale = 2.0, renorm = 97):
        '''Create a Trackball object.  "size" is the radius of the inner trackball
           sphere.  "scale" is a multiplier applied to the mouse coordinates before
           mapping into the viewport.  "renorm" is not currently used.'''

        self.size = size
        self.scale = scale
        self.renorm = renorm
			

    def __track_project_to_sphere(self, px, py):
        d2 = px**2 + py**2
        d = sqrt(d2)
        if d < self.size * 0.70710678118654752440:
            # Inside sphere
            return sqrt(self.size**2 - d2)

        # On hyperbola
        t = self.size/1.41421356237309504880
        return t**2/d


    def update(self, p1x, p1y, p2x, p2y, width, height, mat = 0):
        '''Update the quaterion with a new rotation position derived
           from the first point (p1) and the second point (p2).  The
           the mat parameter is not currently used.'''
    
        if p1x == p2x and p1y == p2y:
            return [1, 0, 0, 0]
        else:
            # First, figure out z-coordinates for projection of p1 and p2 to
            # deformed sphere
            p1x_u = self.scale*p1x/width - 1.0
            p1y_u = 1.0 - self.scale*p1y/height
            p2x_u = self.scale*p2x/width - 1.0
            p2y_u = 1.0 - self.scale*p2y/height

            P1 = (p1x_u,p1y_u,self.__track_project_to_sphere(p1x_u, p1y_u)) 
            P2 = (p2x_u,p2y_u,self.__track_project_to_sphere(p2x_u, p2y_u))

            # FIXME: this is a cross product, could be simplified
            a = [(P2[1]*P1[2]) - (P2[2]*P1[1]),
                 (P2[2]*P1[0]) - (P2[0]*P1[2]),
                 (P2[0]*P1[1]) - (P2[1]*P1[0])]
			
            # Figure out how much to rotate around that axis.
            d = map(lambda x, y: x - y, P1, P2)
            t = sqrt(d[0]**2 + d[1]**2 + d[2]**2) / (2.0 * self.size)

            # Avoid problems with out-of-control values...
            t = max(min(t, 1.0), -1.0)

            if False:
                scale = t*sqrt(a[0]**2 + a[1]**2 + a[2]**2)
                q = map(lambda x, y: x*y, a, [scale]*3) + [sqrt(1.0-t**2)]
                self.quat = quaternion(q[0], q[1], q[2], q[3])
            else:
                # The working C version
                #
                # vnormal(a);
                # vcopy(a,q);
                # vscale(q,(float)sin((double)phi/2.0));
                # q[3] = (float)cos((double)phi/2.0f);

                # vnormal(a);
                phi = 2 * asin(t)

                n = norm(a)
                a = map(lambda x: x/n, a)

                # vcopy(a,q);
                q = range(4)
                q[:3] = a

                # vscale(q,(float)sin((double)phi/2.0));
                q = map(lambda x: x * sin(phi / 2), q)

                # q[3] = (float)cos((double)phi/2.0f);
                q[3] = cos(phi / 2)
                return [q[0], q[1], q[2], q[3]]

	def __getattr__(self, name):
		if name != 'matrix':
			raise AttributeError, 'No attribute named "%s"' % name
		return self.quat.matrix4

def add_quat_wiki(q1, q2):
    ''' http://en.wikipedia.org/wiki/Quaternion '''
    a1, b1, c1, d1 = q1
    a2, b2, c2, d2 = q2

    return [a1*a2 - b1*b2 - c1*c2 - d1*d2,
            a1*b2 + b1*a2 + c1*d2 - d1*c2,
            a1*c2 - b1*d2 + c1*a2 + d1*b2,
            a1*d2 + b1*c2 - c1*b2 + d1*a2]

def vscale(v1, s):
    return map(lambda x: x * s, v1)

def vcopy(v1):
    from copy import deepcopy
    return deepcopy(v1)

def vcross(v1, v2):
    return [ 
            (v1[1] * v2[2]) - (v1[2] * v2[1]), 
            (v1[2] * v2[0]) - (v1[0] * v2[2]), 
            (v1[0] * v2[1]) - (v1[1] * v2[0]) ]

def vdot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def vadd(v1, v2):
    return [v1[0] + v2[0],
            v1[1] + v2[1],
            v1[2] + v2[2]]

def vsub(v1, v2):
    return [v1[0] - v2[0],
            v1[1] - v2[1],
            v1[2] - v2[2]]

def mk_vector(v1, v2):
    return [v2[0] - v1[0],
            v2[1] - v1[1],
            v2[2] - v1[2]]

def vnorm(v):
    N = norm(v)
    try:
        return map(lambda x: x / N, v)
    except:
        return 3 * [0.0]

def add_quat(q1, q2):
    '''
    sdk.pointer_move('rotate', xstart=241, ystart=237, xend=75, yend=108)
    w, h = 387 368
    # should return $2 = {0.453904808, 0.539393365, 0.203423977, 0.679443836}
    '''
    logger.info('add_quat %s %s' % (str(q1), str(q2)))

    t3 = vcross(q2,q1)

    t1 = vcopy(q1)
    t1 = vscale(t1, q2[3])

    t2 = vcopy(q2)
    t2 = vscale(t2, q1[3])

    tf = vadd(t1,t2)
    tf = vadd(t3,tf)
    tf += [None]
    tf[3] = q1[3] * q2[3] - vdot(q1,q2)

    return tf

def rayIntersectsTriangle(p, d, v0, v1, v2):
    ''' http://www.lighthouse3d.com/opengl/maths/index.php?raytriint
    ''' 
    e1 = vsub(v1, v0)
    e2 = vsub(v2, v0)
    h = vcross(d, e2)
    a = vdot(e1, h)

    if a > -0.00001 and a < 0.00001:
        return None

    f = 1.0 / a;
    s = vsub(p, v0)
    u = f * vdot(s, h)

    if u < 0.0 or u > 1.0:
        return None

    q = vcross(s, e1)
    v = f * vdot(d,q);
    if v < 0.0 or u + v > 1.0:
        return None

    # at this stage we can compute t to find out where 
    # the intersection point is on the line
    t = f * vdot(e2,q)
    if t > 0.00001: # ray intersection
        return vadd(p, vscale(d, t))
    else: # this means that there is a line intersection but not a ray intersection
        return None

def rayIntersectsQuad(ray, face):
    ''' FIXME '''
    p, d, = ray
    v0, v1, v2, v3 = face
    return rayIntersectsTriangle(p, d, v0, v1, v2) or \
           rayIntersectsTriangle(p, d, v2, v3, v0)

def build_ray(segment):
    ray = 2*[0.0]
    ray[0] = segment[0]
    ray[1] = vsub(segment[1], segment[0])
    return ray

if __name__ == '__main__':
    p1 = [1, 0, 0]
    p2 = [1, 1, 0]
    p3 = [0, 1, 0]
    k = vcross(sub(p2, p1), sub(p3, p1))
    assert k == [0, 0, 1]

    assert not rayIntersectsTriangle([.2, .2, 1], [10, 10, 10], 
        [0, 0, 0], [0, 1, 0], [1, 0, 0])
    assert rayIntersectsTriangle([.2, .2, 1], [0, 0, -1],
        [0, 0, 0], [0, 1, 0], [1, 0, 0])

    from scene import BoundingBox
    bb = BoundingBox([0, 0, 0], [1, 1, 1])

    assert bb.intersect([ [0.5, 0.5, -0.5], [0.5, 0.5, 1] ])



