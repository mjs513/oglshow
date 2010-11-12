/*
 * Copyright (C) 1999-2001  Brian Paul   All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * BRIAN PAUL BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
 * AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
/* $XFree86: xc/programs/glxgears/glxgears.c,v 1.4 2003/10/24 20:38:11 tsi Exp $ */

/*
 * This is a port of the infamous "gears" demo to straight GLX (i.e. no GLUT)
 * Port by Brian Paul  23 March 2001
 *
 * Command line options:
 *    -info      print GL implementation information
 *
 *
 * Modified by Benjamin Sergeant for oglshow
 * X mouse infos from:
 * http://mx.perchine.com/dyp/x/online/X_event.html#s3.6.5.
 */


#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <X11/Xlib.h>
#include <X11/keysym.h>
#include <GL/gl.h>
#include <GL/glx.h>

// BS
#include "view.h"
static OglSdk sdk;

#include <sys/time.h>
#include <unistd.h>

/* return current time (in seconds) */
static int current_time(void) {
   struct timeval tv;
   struct timezone tz;
   (void) gettimeofday(&tv, &tz);
   return (int) tv.tv_sec;
}

static void reshape(int width, int height, Display *dpy, Window win) {
    sdk.reshape(width, height);
    glXSwapBuffers(dpy, win);
}

static void init(int width, int height) {
}

/*
 * Create an RGB, double-buffered window.
 * Return the window and context handles.
 *
 * See also http://www.opengl.org/sdk/docs/man/xhtml/glXChooseFBConfig.xml
 *
 * See also http://www.google.com/codesearch/p?hl=en#I0cABDTB4TA/pub/FreeBSD/ports/distfiles/MesaDemos-6.5.1.tar.bz2%7CHPWcww5QqTk/Mesa-6.5.1/progs/xdemos/xfont.c&q=glxgears&d=8
 */
static void
make_window( Display *dpy, const char *name,
             int x, int y, int width, int height,
             Window *winRet, GLXContext *ctxRet)
{
   int attrib[] = { GLX_RGBA,
                    GLX_RED_SIZE, 8,
                    GLX_GREEN_SIZE, 8,
                    GLX_BLUE_SIZE, 8,
                    GLX_DOUBLEBUFFER, 1,
                    GLX_DEPTH_SIZE, 1,
                    None };
   int scrnum;
   XSetWindowAttributes attr;
   unsigned long mask;
   Window root;
   Window win;
   GLXContext ctx;
   XVisualInfo *visinfo;

   scrnum = DefaultScreen( dpy );
   root = RootWindow( dpy, scrnum );

   visinfo = glXChooseVisual( dpy, scrnum, attrib );
   if (!visinfo) {
      printf("Error: couldn't get an RGB, Double-buffered visual\n");
      exit(1);
   }

   /* window attributes */
   attr.background_pixel = 0;
   attr.border_pixel = 0;
   attr.colormap = XCreateColormap( dpy, root, visinfo->visual, AllocNone);
   // attr.event_mask = StructureNotifyMask | ExposureMask | KeyPressMask;
   // BS - add trackball
   attr.event_mask = StructureNotifyMask | ExposureMask | KeyPressMask | \
        ButtonPressMask | ButtonReleaseMask | ButtonMotionMask; // | PointerMotionMask;
   mask = CWBackPixel | CWBorderPixel | CWColormap | CWEventMask;

   win = XCreateWindow( dpy, root, 0, 0, width, height,
                        0, visinfo->depth, InputOutput,
                        visinfo->visual, mask, &attr );

   /* set hints and properties */
   {
      XSizeHints sizehints;
      sizehints.x = x;
      sizehints.y = y;
      sizehints.width  = width;
      sizehints.height = height;
      sizehints.flags = USSize | USPosition;
      XSetNormalHints(dpy, win, &sizehints);
      XSetStandardProperties(dpy, win, name, name,
                              None, (char **)NULL, 0, &sizehints);
   }

   ctx = glXCreateContext( dpy, visinfo, NULL, True );
   if (!ctx) {
      printf("Error: glXCreateContext failed\n");
      exit(1);
   }

   XFree(visinfo);

   *winRet = win;
   *ctxRet = ctx;
}


static void
event_loop(Display *dpy, Window win)
{
   while (1) {
      while (XPending(dpy) > 0) {
         XEvent event;
         XNextEvent(dpy, &event);
         switch (event.type) {
         case Expose:
            /* we'll redraw below */
            break;
         case ConfigureNotify:
            reshape(event.xconfigure.width, event.xconfigure.height, dpy, win);
            break;
         case KeyPress:
            {
               char buffer[10];
               int code;
               code = XLookupKeysym(&event.xkey, 0);
               if (code == XK_Left) {
               }
               else if (code == XK_Right) {
               }
               else if (code == XK_Up) {
               }
               else if (code == XK_Down) {
               }
               else {
                  (void) XLookupString(&event.xkey, buffer, sizeof(buffer),
                                    NULL, NULL);
                  if (buffer[0] == 27) {
                     /* escape */
                     return;
                  }
               }
            }
         case ButtonPress: 
            {
                int x = event.xbutton.x;
                int y = event.xbutton.y;

                OglSdk::mouse m = { x, y };
                sdk.mouse_start = m;

                puts("ButtonPress");
                break;
            }
         case ButtonRelease:
            puts("ButtonRelease");
            break;
         case MotionNotify: 
            {
                int x = event.xbutton.x;
                int y = event.xbutton.y;

                string manip_mode("rotate");

            if (event.xbutton.button == 1)
                      manip_mode = "rotate";

                 if (event.xbutton.button == 2)
                      manip_mode = "pan";

                 if (event.xbutton.button == 3)
                      manip_mode = "zoom";
                
                /*
                switch(sdk.button) {
                    case GLUT_LEFT_BUTTON:   manip_mode = "rotate"; break;
                    case GLUT_MIDDLE_BUTTON: manip_mode = "pan";    break;
                    case GLUT_RIGHT_BUTTON:  manip_mode = "zoom";   break;
                }
                */

                sdk.pointer_move(manip_mode, sdk.mouse_start.x, sdk.mouse_start.y, x, y);
                OglSdk::mouse m = { x, y };
                sdk.mouse_start = m;

                puts("MotionNotify");
           }
           break;
      }

      sdk.render();
      glXSwapBuffers(dpy, win);

      /* calc framerate */
      {
         static int t0 = -1;
         static int frames = 0;
         int t = current_time();

         if (t0 < 0)
            t0 = t;

         frames++;

         if (t - t0 >= 5.0) {
            GLfloat seconds = t - t0;
            GLfloat fps = frames / seconds;
            printf("%d frames in %3.1f seconds = %6.3f FPS\n", frames, seconds,
                   fps);
            t0 = t;
            frames = 0;
         }
      }
   }
   }
}


int
main(int argc, char *argv[])
{
   Display *dpy;
   Window win;
   GLXContext ctx;
   char *dpyName = NULL;

   dpy = XOpenDisplay(dpyName);
   if (!dpy) {
      printf("Error: couldn't open display %s\n", dpyName);
      return -1;
   }

   make_window(dpy, "glxview", 0, 0, 300, 300, &win, &ctx);
   XMapWindow(dpy, win);
   glXMakeCurrent(dpy, win, ctx);

   sdk.w = 300;
   sdk.h = 300;
   
   if (argc == 2) {
       sdk.load_file(argv[1]);
   } else {
       sdk.load_file("../../py/test/data/gears.obj");
       // sdk.load_file("../../py/test/data/triangle.obj");
   }
   reshape(300, 300, dpy, win);

   event_loop(dpy, win);

   glXDestroyContext(dpy, ctx);
   XDestroyWindow(dpy, win);
   XCloseDisplay(dpy);

   return 0;
}
