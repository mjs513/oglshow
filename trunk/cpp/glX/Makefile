all: glxview

glxgears:
	gcc -o glxgears glxgears.c -lX11 -lGL -I/usr/X11/include -L/usr/X11/lib

glxview: glxview.cc
	g++ -o glxview glxview.cc -lX11 -lGL -lGLU -I../glut -I/usr/X11/include -L/usr/X11/lib
