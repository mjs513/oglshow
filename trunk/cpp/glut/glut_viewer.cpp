
/* Basic .obj OpenGL Viewer, by Benjamin Sergeant */
/* g++ -framework GLUT -framework OpenGL -framework Cocoa glut_viewer.cpp -o robot */

#include "view.h"

static OglSdk sdk;

void ogl_motion(int x, int y) {
    string manip_mode("rotate");
    switch(sdk.button) {
        case GLUT_LEFT_BUTTON:   manip_mode = "rotate"; break;
        case GLUT_MIDDLE_BUTTON: manip_mode = "pan";    break;
        case GLUT_RIGHT_BUTTON:  manip_mode = "zoom";   break;
    }

    sdk.pointer_move(manip_mode, sdk.mouse_start.x, sdk.mouse_start.y, x, y);
    OglSdk::mouse m = { x, y };
    sdk.mouse_start = m;

    glutPostRedisplay(); // # ask for a refresh
}

void ogl_mouse(int button, int button_state, int x, int y) {
    sdk.button = button;
    sdk.motion = button_state;
    OglSdk::mouse m = { x, y };
    sdk.mouse_start = m;

    glutPostRedisplay(); // ask for a refresh
}

// FIXME: This should go in a timer|chrono.h file
#include <mach/mach_time.h>  
#include <time.h>  
#include <stdio.h>  

// MacOSX
// http://www.wand.net.nz/~smr26/wordpress/2009/01/19/monotonic-time-in-mac-os-x/
// Linux
// Check http://www.opengroup.org/onlinepubs/007908799/xsh/clock_gettime.html
class Chrono
{
public:
    Chrono() {
        start = mach_absolute_time();  
    }
    void get() {
        end = mach_absolute_time();  
        struct timespec tp;  
        mach_absolute_difference(end, start, &tp);  
        printf("%lu seconds, %09lu nanoseconds %d fps\n", 
            tp.tv_sec, tp.tv_nsec, (int) (1.0f / (tp.tv_nsec/1e9)));  
    }
    void mach_absolute_difference(uint64_t end, uint64_t start, 
                                  struct timespec *tp) {  
        uint64_t difference = end - start;  
        static mach_timebase_info_data_t info = {0,0};  

        if (info.denom == 0)  
            mach_timebase_info(&info);  

        uint64_t elapsednano = difference * (info.numer / info.denom);  

        tp->tv_sec = elapsednano * 1e-9;  
        tp->tv_nsec = elapsednano - (tp->tv_sec * 1e9);  
    }  

    uint64_t start,end;  
};
  
void ogl_display(void) {
    Chrono c;
    sdk.render();
    // FIXME glutSetWindowTitle('FPS: ' + sdk.fps)'
    glutSwapBuffers(); 
    c.get();
}

void ogl_reshape(int w, int h) {
    sdk.reshape(w, h);
    glutSwapBuffers();
}

void ogl_processNormalKeys(unsigned char key, int x, int y) {
    if (key == 27)
        exit(0);
}

int main(int argc, char** argv) {
    sdk.w = 600;
    sdk.h = 480;

    if (argc == 2) {
        sdk.load_file(argv[1]);
    } else {
        sdk.load_file("../../py/test/data/gears.obj");
        // sdk.load_file("../../py/test/data/triangle.obj");
    }

    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH);

    // glutInitWindowPosition(100, 100):
    glutInitWindowSize(sdk.w, sdk.h);
    (void)glutCreateWindow("oglshow");

    glutKeyboardFunc(ogl_processNormalKeys);

    // Mouse
    glutMouseFunc(ogl_mouse);
    glutMotionFunc(ogl_motion);

    glutDisplayFunc(ogl_display);
    glutReshapeFunc(ogl_reshape);

    glutMainLoop();
}

