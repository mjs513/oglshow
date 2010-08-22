#pragma once

#include <vector>
#include <limits>

#include <stdio.h>

using std::vector;
using std::min;
using std::max;
using std::numeric_limits;

#include "math_utils.h"

// FIXME: pass vertex as const&
class BoundingBox
{
public:
    float xmin, ymin, zmin;
    float xmax, ymax, zmax;

    BoundingBox() {
        float big = numeric_limits<float>::max();
        xmin =  big; ymin =  big; zmin =  big; 
        xmax = -big; ymax = -big; zmax = -big;
    }

    void add_points(const vector<vertex>& verts) {
        for (size_t i = 0; i < verts.size(); ++i) {
            add_point(verts[i]);
        }
    }

    void add_point(vertex v) {
        xmin = std::min(v.x, xmin);
        ymin = std::min(v.y, ymin);
        zmin = std::min(v.z, zmin);

        xmax = std::max(v.x, xmax);
        ymax = std::max(v.y, ymax);
        zmax = std::max(v.z, zmax);
    }

    void print() {
        printf("xmin %f xmax %f\n", xmin, xmax);
        printf("ymin %f ymax %f\n", ymin, ymax);
        printf("zmin %f zmax %f\n", zmin, zmax);
    }
    float sphere_beam() {
        return distance(max(), min()) / 2;
    }
    vertex center() {
        vertex v = { (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2 };
        return v;
    }
    vertex min() {
        vertex v = { xmin, ymin, zmin };
        return v;
    }
    vertex max() {
        vertex v = { xmax, ymax, zmax };
        return v;
    }
};

class View
{
public:
    float recenterX;
    float recenterY;
    float focal;
    quaternion quat;
    vertex eye;
    vertex tget;
    float roll;

    View() {
        recenterX = 0.0;
        recenterY = 0.0;
        focal = 0.0;

        quaternion null_quat = { 0 };
        vertex null_vert = { 0 };

        quat = null_quat;
        eye = null_vert;
        tget = null_vert;
        roll = 0.0;
    }

    void reset(BoundingBox _bb) {
        recenterX = 0.0;
        recenterY = 0.0;
        focal = 32.0;
        quat = common_quaternion_from_angles(180, 45+22.5, 0 );

        float recul = 2.0 * _bb.sphere_beam();

        // Using sub(_bb.min(), [recul, recul, recul]) has the same effects
        vertex recul_v = { recul, recul, recul };
        eye = add(recul_v, _bb.max());
        tget = _bb.center();
    }

    void print() {
        printf("Quat ");
        print_quaternion(quat);
        printf("Eye ");
        print_vert(eye);
        printf("Target ");
        print_vert(tget);
        printf("Focal %f\n", focal);
        printf("Roll %f\n", roll);
        printf("recenterX %f\n", recenterX);
        printf("recenterY %f\n", recenterY);
    }
};

class Scene
{
public:
    vector<vertex> verts;
    vector<face> faces;
    vector<vertex> normals;
    vector<face> faces_normals;
    BoundingBox bb;
    View view;

    Scene() {}
    void read(const char* fn) {
        FILE* f = fopen(fn, "r");
        if (f != NULL) {
            for (;;) {
                char buf[1024];
                if (!fgets(buf, sizeof(buf), f)) break;

                if (buf[0] == 'v' && buf[1] == ' ') {
                    vertex p;
                    sscanf(buf+2, "%f %f %f", &p.x, &p.y, &p.z);
                    verts.push_back(p);
                    bb.add_point(p);
                }
                if (buf[0] == 'v' && buf[1] == 'n') {
                    vertex n;
                    sscanf(buf+2, "%f %f %f", &n.x, &n.y, &n.z);
                    normals.push_back(n);
                }
                if (buf[0] == 'f') {
                    char p1[255];
                    bool has_normals = false;
                    int f1, f2, f3, f4;
                    int n1, n2, n3, n4;
                    int tmp;
                    int cnt = sscanf(buf+2, "%s %s %s %s", p1, p1, p1, p1);

                    if (strchr(p1, '/') == NULL) {
                        if (cnt == 3)
                            sscanf(buf+2, "%d %d %d", &f1, &f2, &f3); 
                        else
                            sscanf(buf+2, "%d %d %d", &f1, &f2, &f3); 
                    } else {
                        has_normals = true;
                        if (strstr(p1, "//"))
                            if (cnt == 3)
                                sscanf(buf+2, "%d//%d %d//%d %d//%d", 
                                    &f1, &n1, &f2, &n2, &f3, &n3);
                            else
                                sscanf(buf+2, "%d//%d %d//%d %d//%d %d//%d", 
                                    &f1, &n1, &f2, &n2, &f3, &n3, &f4, &n4);
                        else
                            if (cnt == 3) 
                                sscanf(buf+2, "%d/%d/%d %d/%d/%d %d/%d/%d", 
                                    &f1, &tmp, &n1, &f2, &tmp, &n2, &f3, &tmp, &n3);
                            else
                                sscanf(buf+2, "%d/%d/%d %d/%d/%d %d/%d/%d %d/%d/%d", 
                                    &f1, &tmp, &n1, &f2, &tmp, &n2, &f3, &tmp, &n3, &f4, &tmp, &n4);
                    }

                    face f = { f1 - 1, f2 -1, f3 -1 };
                    faces.push_back(f);

                    if (cnt == 4) {
                        face g = { f3 - 1, f4 -1, f1 -1 };
                        faces.push_back(g);
                    }

                    if (has_normals) {
                        face n = { n1 - 1, n2 -1, n3 -1 };
                        faces_normals.push_back(n);

                        if (cnt == 4) {
                            face p = { n3 - 1, n4 -1, n1 -1 };
                            faces_normals.push_back(p);
                        }
                    }
                }
            }
        }

        fclose(f);
    }
    void compute_bb() {
        bb.add_points(verts);
    }
    void print(bool geom = false) {
        printf("%zu verts, %zu faces, %zu normals %zu faces_normals\n", 
            verts.size(), faces.size(), normals.size(), faces_normals.size()); 

        if (geom) {
            for (size_t i = 0; i < faces.size(); ++i) {
                face f = faces[i];
                printf("%d %d %d\n", f.p1, f.p2, f.p3);

                if (! faces_normals.empty()) {
                    face fn = faces_normals[i];
                    printf("%d %d %d\n", fn.p1, fn.p2, fn.p3);
                }
            }
        }
    }
};

extern Scene load(const char* fn) {
    Scene sc;
    sc.read(fn);
    sc.compute_bb();
    sc.view.reset(sc.bb);
    return sc;
}
