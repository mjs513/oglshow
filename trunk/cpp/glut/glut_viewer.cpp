
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

void ogl_display(void) {
    Chrono c;
    sdk.render();
    // FIXME glutSetWindowTitle('FPS: ' + sdk.fps)'
    glutSwapBuffers(); 
    c.get();

#define        GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX          0x9047
#define        GPU_MEMORY_INFO_TOTAL_AVAILABLE_MEMORY_NVX    0x9048
#define        GPU_MEMORY_INFO_CURRENT_AVAILABLE_VIDMEM_NVX  0x9049
#define        GPU_MEMORY_INFO_EVICTION_COUNT_NVX            0x904A
#define        GPU_MEMORY_INFO_EVICTED_MEMORY_NVX            0x904B

    GLint dedicated, total, current;
    glGetIntegerv(GPU_MEMORY_INFO_TOTAL_AVAILABLE_MEMORY_NVX, &total);
    glGetIntegerv(GPU_MEMORY_INFO_TOTAL_AVAILABLE_MEMORY_NVX, &total);
    glGetIntegerv(GPU_MEMORY_INFO_CURRENT_AVAILABLE_VIDMEM_NVX, &current);
    printf("dedicated %d total %d current %d\n", dedicated, total, current);
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
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH | GLUT_MULTISAMPLE);

    // glutInitWindowPosition(100, 100):
    glutInitWindowSize(sdk.w, sdk.h);
    (void)glutCreateWindow("oglshow");
    glewInit();

    glutKeyboardFunc(ogl_processNormalKeys);

    // Mouse
    glutMouseFunc(ogl_mouse);
    glutMotionFunc(ogl_motion);

    glutDisplayFunc(ogl_display);
    glutReshapeFunc(ogl_reshape);

    glutMainLoop();
}

