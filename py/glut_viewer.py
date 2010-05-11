#!/usr/bin/env python
# env python works on Mac while /usr/bin/python does not ...

from sys import argv, exit

from utils import _err_exit, notYetImplemented
from scene import ArgsOptions

try:
    from OpenGL.GLUT import *
except ImportError:
    _err_exit('ERROR: PyOpenGL not installed properly.')

window_title = 'Python GLUT obj viewer'
window_title = ''

def ogl_motion(x, y):
    manip_mode = {
            GLUT_LEFT_BUTTON: 'rotate',
            GLUT_MIDDLE_BUTTON: 'pan',
            GLUT_RIGHT_BUTTON: 'zoom'
            }
    sdk.pointer_move(manip_mode.get(sdk.button, 'rotate'), 
            sdk.mouse_start[0], sdk.mouse_start[1], x, y)
    sdk.mouse_start = [x, y]

    glutPostRedisplay() # ask for a refresh

def ogl_mouse(button, button_state, x, y):
    sdk.button = button
    sdk.motion = button_state
    sdk.mouse_start = [x, y]

def ogl_display():
    sdk.render()
    glutSetWindowTitle('FPS: ' + sdk.fps)
    # glutSwapBuffers() # not required as we pass it to the sdk

def ogl_reshape(w, h):
    sdk.reshape(w, h)
    # glutSwapBuffers() # not required as we pass it to the sdk

# Keyboard
def ogl_processNormalKeys(key, x, y):
    if ord(key) == 27:
        exit(0)
    if key == 'a':
        sdk.start_conference_as_slave()

def glut_main(w, h):
    '''
    Declare initial window size, position, and display mode
    (single buffer and RGBA).  Open window with "hello"
    in its title bar.  Call initialization routines.
    Register callback function to display graphics.
    Enter main loop and process events.
    '''
    glutInit(argv)
    # Modes: GLUT_SINGLE
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)

    glutInitWindowSize(sdk.w, sdk.h)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(window_title)

    glutKeyboardFunc(ogl_processNormalKeys)

    # Mouse
    glutMouseFunc(ogl_mouse);
    glutMotionFunc(ogl_motion);

    glutDisplayFunc(ogl_display)
    glutReshapeFunc(ogl_reshape)

    glutMainLoop()

if __name__ == '__main__':

    ao = ArgsOptions()
    options = [ao.options.fn,
               ao.options.verbose,
               ao.options.procedural]

    # Window dimensions
    w, h = 600, 480 

    from viewer import OglSdk
    sdk = OglSdk(w, h, glutSwapBuffers)
    sdk.load_file(*options)

    glut_main(w, h)
