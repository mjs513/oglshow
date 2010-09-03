#pragma once

#include <string>
#include <iostream>
using std::string;
using std::cout;
using std::endl;

#include <GLUT/glut.h>
#include "scene.h"

class OglSdk
{
public:
    int w, h;
    typedef struct mouse { int x, y; };
    mouse mouse_start;
    int button, motion;
    Scene scene;
    Trackball trackball;

    OglSdk() {}

    void load_file(const char* fn) {
        scene = load(fn);
        scene.print(true);
    }

    void pointer_move(string m, int xstart, int ystart, int xend, int yend) {
        cout << m << " " << xstart << " " << ystart << " " << xend << " " << yend << endl;
        float ww = w;
        float wh = h;

        if (m == "zoom") {
            float dx = xstart - xend;
            float dy = ystart - yend;
            float rate = (fabs(dy) > fabs(dx)) ? dy / wh : dx / ww;

            scene.view.focal *= 1.0 - rate;

        } else if (m == "pan") {
            float prevX = (2.0 * xstart - ww) / ww;
            float prevY = (2.0 * ystart - wh) / wh;
            float newX = (2.0 * xend - ww) / ww;
            float newY = (2.0 * yend - wh) / wh;

            float window_ratio = ww / wh;

            // (from Antoine) je met au milieu de la distance oeil,cible en
            // translate les objets + proches bougeront + vite et les +
            // lointains moins vite 

            const float DEFAULT_ZOOM = 32.0;
            float k = scene.bb.sphere_beam();

            scene.view.recenterX += -k*(scene.view.focal/DEFAULT_ZOOM) * window_ratio * (prevX - newX);
            scene.view.recenterY +=  k*(scene.view.focal/DEFAULT_ZOOM) * (prevY - newY);
        } else if (m == "rotate") {
            quaternion spin_quat = trackball.update(xstart, ystart, xend, yend, ww, wh);
            print_quaternion(spin_quat);
            scene.view.quat = add_quat(spin_quat, scene.view.quat);
            print_quaternion(scene.view.quat);
        }
    }

#if 0
    void set_matrix_nehe_sample()
    {
        glMatrixMode(GL_PROJECTION);						// Select The Projection Matrix
        glLoadIdentity();							// Reset The Projection Matrix

        // Calculate The Aspect Ratio Of The Window
        gluPerspective(45.0f,(GLfloat)w/(GLfloat)h,0.1f,100.0f);

        glMatrixMode(GL_MODELVIEW);						// Select The Modelview Matrix
        glLoadIdentity();
    }
    // Debug
    void draw_nehe_sample() {

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);		// Clear The Screen And The Depth Buffer
        glLoadIdentity();
    
        glTranslatef(-1.5f,0.0f,-6.0f);	
        glBegin(GL_TRIANGLES);						// Drawing Using Triangles
            glVertex3f( 0.0f, 1.0f, 0.0f);				// Top
            glVertex3f(-1.0f,-1.0f, 0.0f);				// Bottom Left
            glVertex3f( 1.0f,-1.0f, 0.0f);				// Bottom Right
        glEnd();							// Finished Drawing The Triangle
    }
#endif
    void draw_bg() {
        glDisable(GL_DEPTH_TEST);
    
        glMatrixMode(GL_PROJECTION);
        glPushMatrix();
        glLoadIdentity();

        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        glDisable(GL_LIGHTING);

        glBegin(GL_QUADS);
        glColor3ub(24, 26, 28); // Bottom / Blue
        glVertex2f(-1.0,-1.0);
        glVertex2f(1.0,-1.0);
        
        glColor3ub(126, 145, 165); // Top / Red
        glVertex2f(1.0, 1.0);
        glVertex2f(-1.0, 1.0);
        glEnd();

        glMatrixMode(GL_PROJECTION);
        glPopMatrix();
        glMatrixMode(GL_MODELVIEW);

        glEnable(GL_DEPTH_TEST);
    }

    void set_default_light(int kind = 2) {
       if (kind == 1) {
           GLfloat mat_specular[] = { 1.0, 1.0, 1.0, 1.0 };
           GLfloat mat_shininess[] = { 50.0 };
           GLfloat light_position[] = { 1.0, 1.0, 1.0, 0.0 };
           glClearColor (0.0, 0.0, 0.0, 0.0);
           glShadeModel (GL_SMOOTH);

           glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular);
           glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess);
           glLightfv(GL_LIGHT0, GL_POSITION, light_position);

           glEnable(GL_LIGHTING);
           glEnable(GL_LIGHT0);
           glEnable(GL_DEPTH_TEST);
       } else if (kind == 2) {
           GLfloat ambiant = 0.22;
           GLfloat mat_ambiant[] = { ambiant, ambiant, ambiant, 1.0 };
           GLfloat mat_diffuse[] = { 1.0 - ambiant, 1.0 - ambiant, 1.0 - ambiant, 1.0 };
           GLfloat mat_specular[] = { 1.0, 1.0, 1.0, 1.0 };
           GLfloat mat_shininess[] = { 60.0 };
           GLfloat light_position[] = { 1.0, 1.0, 1.0, 0.0 };
           glClearColor (0.0, 0.0, 0.0, 0.0);

           glLightModelfv(GL_LIGHT_MODEL_AMBIENT, mat_ambiant);

           // Light 0
           glLightfv(GL_LIGHT0, GL_POSITION, light_position);
           glLightfv(GL_LIGHT0, GL_DIFFUSE, mat_diffuse);
           glLightfv(GL_LIGHT0, GL_SPECULAR, mat_diffuse); // cannot see that ...
           glLightfv(GL_LIGHT0, GL_SHININESS, mat_shininess);

           // Light 1
           GLfloat mat1_diffuse[] = { 1.0, 1.0, 1.0, 1.0 };
           GLfloat light1_position[] = { -0.7, -0.7, -0.7, 0.0 };
           glLightfv(GL_LIGHT1, GL_POSITION, light1_position);
           glLightfv(GL_LIGHT1, GL_DIFFUSE, mat1_diffuse);
           glLightfv(GL_LIGHT1, GL_SPECULAR, mat_diffuse);
           glLightfv(GL_LIGHT1, GL_SHININESS, mat_shininess);

           glShadeModel(GL_SMOOTH);
           glLightModelf(GL_LIGHT_MODEL_TWO_SIDE, 1.0);
           glEnable(GL_COLOR_MATERIAL);
           glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);
           glEnable(GL_LIGHTING);
           glEnable(GL_LIGHT0);
           // glEnable(GL_LIGHT1);
           glEnable(GL_DEPTH_TEST);
       }
    }

    void init_gl() { // from nehe
        glEnable(GL_MULTISAMPLE_ARB);

        glShadeModel(GL_SMOOTH);	           // Enables Smooth Shading
        glClearColor(0.0f, 0.0f, 0.0f, 0.0f);  // Black Background
        glClearDepth(1.0f);                    // Depth Buffer Setup
        glEnable(GL_DEPTH_TEST);               // Enables Depth Testing
        glDepthFunc(GL_LEQUAL);                // The Type Of Depth Test To Do
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, // Really Nice Perspective Calculations
               GL_NICEST);
    }

    void render() {
        init_gl();
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        draw_bg();
        set_default_light();
        set_matrix(scene.view);
        render_obj();
    }

    void render_obj() {
        // Clear The Screen And The Depth Buffer

        GLubyte diffuse[3] = { 51.0, 51.0, 255.0 };
        glColor3ubv( diffuse );

        glBegin(GL_TRIANGLES);
        for (size_t i = 0; i < scene.faces.size(); ++i) {

            face f = scene.faces[i];
            if (! scene.faces_normals.empty()) {
                face fn = scene.faces_normals[i];
                glNormal3f( scene.normals[fn.p1].x, 
                            scene.normals[fn.p1].y,  
                            scene.normals[fn.p1].z );
                glVertex3f( scene.verts[f.p1].x, scene.verts[f.p1].y, scene.verts[f.p1].z );
                glNormal3f( scene.normals[fn.p2].x, 
                            scene.normals[fn.p2].y,
                            scene.normals[fn.p2].z );
                glVertex3f( scene.verts[f.p2].x, scene.verts[f.p2].y, scene.verts[f.p2].z );
                glNormal3f( scene.normals[fn.p3].x, 
                            scene.normals[fn.p3].y,
                            scene.normals[fn.p3].z );
                glVertex3f( scene.verts[f.p3].x, scene.verts[f.p3].y, scene.verts[f.p3].z );
            } else {
                glVertex3f( scene.verts[f.p1].x, scene.verts[f.p1].y, scene.verts[f.p1].z );
                glVertex3f( scene.verts[f.p2].x, scene.verts[f.p2].y, scene.verts[f.p2].z );
                glVertex3f( scene.verts[f.p3].x, scene.verts[f.p3].y, scene.verts[f.p3].z );
            }
        }
        glEnd();
    }

    void reshape(int _w, int _h) {
        glViewport(0, 0, w, h);
        w = _w;
        h = _h;
    }

    void set_matrix(View& view) {
        puts("set_matrix");

        // Projection
        glMatrixMode( GL_PROJECTION );
        glLoadIdentity();

        float pixel_ratio = w / (float)h;
        float zF = view.focal / 30.0;

        float diam2 = 2.0 * scene.bb.sphere_beam();

        vertex look = sub(view.tget, view.eye);
        float diam = 0.5 * norm(look);
        float recul = 2 * diam;

        float zNear = 0.01 * recul; // 1% du segment de visee oeil-cible
        float zFar = recul + diam2;

        if (pixel_ratio < 1)
            zF /= pixel_ratio;

        if (true) printf("gluPerspective %f %f %f %f\n", zF*30, pixel_ratio, zNear, zFar);
        gluPerspective (zF*30, pixel_ratio, zNear, zFar);

        // Model View
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();

        glTranslatef(view.recenterX, view.recenterY, 0.0);

        // Take care of the eye
        matrix rotation_matrix = quaternion_to_matrix(view.quat);
        vertex new_look = { 0, 0, recul }; // LOL name
        view.eye = multiply_point_by_matrix(rotation_matrix, new_look);
        view.eye = add(view.eye, scene.bb.center());

        // Vector UP (Y)
        vertex yup = { 0.0, 1.0, 0.0 };
        vertex vup = multiply_point_by_matrix(rotation_matrix, yup);

        // debug
        if (true) {
            printf("gluLookAt eye ");
            print_vert(view.eye);
            printf("gluLookAt tget ");
            print_vert(view.tget);
            printf("gluLookAt vup ");
            print_vert(vup);
        }
        
        gluLookAt (	view.eye.x,  view.eye.y,  view.eye.z,
                    view.tget.x, view.tget.y, view.tget.z,
                    vup.x,  vup.y,  vup.z  );
    }
};
