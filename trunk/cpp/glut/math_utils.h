#pragma once

#include <math.h>
#include <algorithm>

typedef struct vertex { float x, y, z; };
typedef struct face   { int p1, p2, p3; };
typedef struct quaternion { float qx, qy, qz, qw; };
typedef struct matrix { float m00, m01, m02,
                              m10, m11, m12,
                              m20, m21, m22; };

inline float square(float v) {
    return v * v;
}

matrix quaternion_to_matrix(quaternion quat) {
    float qx = quat.qx;
    float qy = quat.qy;
    float qz = quat.qz;
    float qw = quat.qw;

    matrix m = {
        1 - 2*square(qy) - 2*square(qz), 
            2*qx*qy - 2*qz*qw,
            2*qx*qz + 2*qy*qw,
        2*qx*qy + 2*qz*qw,	
            1 - 2*square(qx) - 2*square(qz), 
            2*qy*qz - 2*qx*qw,
        2*qx*qz - 2*qy*qw,
            2*qy*qz + 2*qx*qw,
            1 - 2*square(qx) - 2*square(qy) 
    };

    return m;
}

vertex multiply_point_by_matrix(matrix mat, vertex p) {
    vertex v = { mat.m00 * p.x + mat.m01 * p.y + mat.m02 * p.z, 
			     mat.m10 * p.x + mat.m11 * p.y + mat.m12 * p.z,
			     mat.m20 * p.x + mat.m21 * p.y + mat.m22 * p.z };
    return v;
}

void print_quaternion(quaternion q) {
    printf("%f %f %f %f\n", q.qx, q.qy, q.qz, q.qw);
}
void print_vert(vertex v) {
    printf("%f %f %f\n", v.x, v.y, v.z);
}

quaternion common_quaternion_from_angles(float fYaw, float fPitch, float fRoll) {
    quaternion quat = { 0 };
    float degre2rad = M_PI / 180.0;

    fYaw *= degre2rad;
    fPitch *= degre2rad;
    fRoll *= degre2rad;

    float fSinYaw   = sin( fYaw*0.5 );
    float fSinPitch = sin( fPitch*0.5 );
    float fSinRoll  = sin( fRoll*0.5 );
    float fCosYaw   = cos( fYaw*0.5 );
    float fCosPitch = cos( fPitch*0.5 );
    float fCosRoll  = cos( fRoll*0.5 );

    quat.qx = fSinRoll * fCosPitch * fCosYaw;
    quat.qy = fCosRoll * fSinPitch * fCosYaw;
    quat.qz = fCosRoll * fCosPitch * fSinYaw;
    quat.qw = fCosRoll * fCosPitch * fCosYaw;

    quat.qx -= fCosRoll * fSinPitch * fSinYaw;
    quat.qy += fSinRoll * fCosPitch * fSinYaw;
    quat.qz -= fSinRoll * fSinPitch * fCosYaw;
    quat.qw += fSinRoll * fSinPitch * fSinYaw;

    return quat;
}

// FIXME: pass vertex as const&
vertex add(vertex A, vertex B) {
    vertex v = { A.x + B.x, A.y + B.y, A.z + B.z };
    return v;
}
vertex sub(vertex A, vertex B) {
    vertex v = { A.x - B.x, A.y - B.y, A.z - B.z };
    return v;
}
float norm(vertex v) {
    return sqrt( square(v.x) + square(v.y) + square(v.z) );
}
float distance(vertex A, vertex B) {
    return norm( sub(A, B) );
}

void qscale(quaternion& q, float s) {
    q.qx *= s;
    q.qy *= s;
    q.qz *= s;
    q.qw *= s;
}
void vscale(vertex& v, float s) {
    v.x *= s;
    v.y *= s;
    v.z *= s;
}
vertex vcross(vertex v1, vertex v2) {
    vertex v = {
        v1.y * v2.z - v1.z * v2.y, 
        v1.z * v2.x - v1.x * v2.z, 
        v1.x * v2.y - v1.y * v2.x
    };
    return v;
}

// vertex should be vectors here
float vdot(vertex v1, vertex v2) {
    return v1.x*v2.x + v1.y*v2.y + v1.z*v2.z;
}
// vertex should be vectors here
vertex vadd(vertex v1, vertex v2) {
    vertex v = { v1.x + v2.x, v1.y + v2.y, v1.z + v2.z };
    return v;
}

vertex vnorm(vertex v1) {
    float inv_N = 1.0f / norm(v1);
    vertex v = { v1.x * inv_N, v1.y * inv_N, v1.z * inv_N };
    return v;
}
// vertex should be vectors here
// this is different from a regular quat (bad name)
quaternion add_quat(quaternion q1, quaternion q2) {
    vertex t1 = { q1.qx, q1.qy, q1.qz };
    vertex t2 = { q2.qx, q2.qy, q2.qz };

    vertex t3 = vcross(t2, t1);

    vscale(t1, q2.qw);
    vscale(t2, q1.qw);

    vertex tf = vadd(t1, t2);
    tf = vadd(t3, tf);

    vertex q1_copy = { q1.qx, q1.qy, q1.qz };
    vertex q2_copy = { q2.qx, q2.qy, q2.qz };
    quaternion q = { tf.x, tf.y, tf.z, q1.qw * q2.qw - vdot(q1_copy, q2_copy) };

    return q;
}


// A trackball object.  This is deformed trackball which is a hyperbolic
// sheet of rotation away from the center. This particular function was chosen
// after trying out several variations.  The current transformation matrix
// can be retrieved using the "matrix" attribute.
class Trackball
{
public:
    float size, scale, renorm;

    // Create a Trackball object.  "size" is the radius of the inner trackball
    // sphere.  "scale" is a multiplier applied to the mouse coordinates before
    // mapping into the viewport.  "renorm" is not currently used.
    Trackball() : size(0.8), scale(2.0), renorm(97) {}

    float __track_project_to_sphere(float px, float py) {
        float d2 = square(px) + square(py);
        float d = sqrt(d2);
        if (d < size * 0.70710678118654752440) // Inside sphere
            return sqrt(square(size) - d2);

        // On hyperbola
        float t = size / 1.41421356237309504880;
        return square(t) / d;
    }

    quaternion update(float p1x, float p1y, float p2x, float p2y, float width, float height) {
        // Update the quaternion with a new rotation position derived
        // from the first point (p1) and the second point (p2).  The
        // the mat parameter (used to be the last optional parameter) is not currently used.
    
        if (p1x == p2x && p1y == p2y) {
            quaternion q = { 1.0, 0.0, 0.0, 0.0 };
            return q;
        } else {
            // First, figure out z-coordinates for projection of p1 and p2 to
            // deformed sphere
            float p1x_u = scale*p1x/width - 1.0;
            float p1y_u = 1.0 - scale*p1y/height;
            float p2x_u = scale*p2x/width - 1.0;
            float p2y_u = 1.0 - scale*p2y/height;

            vertex P1 = { p1x_u, p1y_u, __track_project_to_sphere(p1x_u, p1y_u) }; 
            vertex P2 = { p2x_u, p2y_u, __track_project_to_sphere(p2x_u, p2y_u) };

            vertex a = vcross(P2, P1);
			
            // Figure out how much to rotate around that axis.
            vertex d = sub(P1, P2);
            float t = norm(d) / (2.0 * size);

            // Avoid problems with out-of-control values...
            t = std::max(std::min(t, 1.0f), -1.0f);

            float phi = 2 * asin(t);
            float n = norm(a);
            vscale(a, 1.0/n);

            quaternion q = { a.x, a.y, a.z, 0.0 };
            qscale(q, (float) sin ((double)phi/2.0));

            q.qw = (float)cos((double)phi/2.0f);
            return q;
        }
    }
};
