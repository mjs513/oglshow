
#include "Python.h"
#include <locale.h>

/* Use this to raise an exception then return NULL;
 * PyErr_SetString(PyExc_ValueError, "String too big, cannot compress.");
 */

static PyObject *
obj_read(PyObject *self, PyObject *args)
{
	/* The :compress tells PyArg_ParseTuple what function to use 
	 * in its error message
	 */
	char *pstr;
	if (!PyArg_ParseTuple(args, "s:read", &pstr)) {
		return NULL;
	}

	PyFileObject* f;
	f = PyFile_FromString((char*) pstr, "r");
	int bufsize = -1;

	PyObject* triangles = PyList_New(0);
	PyObject* points = PyList_New(0);

	if (f != NULL) {
		PyFile_SetBufSize(f, bufsize);

		for (;;) {
			/* From PyFile_GetLine doc
			 *
			 * If n is 0, exactly one line is read,
			 * regardless of the length of the line. If n is
			 * greater than 0, no more than n bytes will be read
			 * from the file; a partial line can be returned. In
			 * both cases, an empty string is returned if the end
			 * of the file is reached immediately.
			 */
			PyObject* line = PyFile_GetLine(f, 0);

			/* Invalid line ? */
			if (! line || ! PyString_Check(line)) break;

			/* Empty line ? */
			int num = PyString_Size(line); 
			if (num == 0) break;

			/*
			 * sscanf params
			 * http://www.cs.utah.edu/~zachary/isp/tutorials/io/io.html
			 */
			char* cline = PyString_AsString(line);
			if (cline[0] == 'f') {
				int a, b, c;
				PyObject* triangle = PyList_New(3);
				sscanf(cline+2, "%d %d %d", &a, &b, &c);

				PyList_SetItem(triangle, 0, PyInt_FromLong(a-1));
				PyList_SetItem(triangle, 1, PyInt_FromLong(b-1));
				PyList_SetItem(triangle, 2, PyInt_FromLong(c-1));

				PyList_Append(triangles, triangle);
			}
			else if (cline[0] == 'v') {
				double a, b, c;
				PyObject* vertex = PyList_New(3);
				sscanf(cline+2, "%lf %lf %lf", &a, &b, &c);

				// printf("%lf %lf %lf\n", a, b, c);

				PyList_SetItem(vertex, 0, PyFloat_FromDouble(a));
				PyList_SetItem(vertex, 1, PyFloat_FromDouble(b));
				PyList_SetItem(vertex, 2, PyFloat_FromDouble(c));

				PyList_Append(points, vertex);
			}
		}
	}
	fclose(PyFile_AsFile(f));

	PyObject* pair = PyList_New(2);
	PyList_SetItem(pair, 0, points);
	PyList_SetItem(pair, 1, triangles);

	return pair;
}

typedef double GLdouble;
typedef int GLint;
#define GL_FALSE 0
#define GL_TRUE 1

static void __gluMultMatrixVecd(const GLdouble matrix[16], const GLdouble in[4],
                      GLdouble out[4])
{
    int i;

    for (i=0; i<4; i++) {
        out[i] =
            in[0] * matrix[0*4+i] +
            in[1] * matrix[1*4+i] +
            in[2] * matrix[2*4+i] +
            in[3] * matrix[3*4+i];
    }
}

GLint 
gluProject(GLdouble objx, GLdouble objy, GLdouble objz,
              const GLdouble modelMatrix[16],
              const GLdouble projMatrix[16],
              const GLint viewport[4],
              GLdouble *winx, GLdouble *winy, GLdouble *winz)
{
    double in[4];
    double out[4];

    in[0]=objx;
    in[1]=objy;
    in[2]=objz;
    in[3]=1.0;
    __gluMultMatrixVecd(modelMatrix, in, out);
    __gluMultMatrixVecd(projMatrix, out, in);
    if (in[3] == 0.0) return(GL_FALSE);
    in[0] /= in[3];
    in[1] /= in[3];
    in[2] /= in[3];
    /* Map x, y and z to range 0-1 */
    in[0] = in[0] * 0.5 + 0.5;
    in[1] = in[1] * 0.5 + 0.5;
    in[2] = in[2] * 0.5 + 0.5;

    /* Map x,y to viewport */
    in[0] = in[0] * viewport[2] + viewport[0];
    in[1] = in[1] * viewport[3] + viewport[1];

    *winx=in[0];
    *winy=in[1];
    *winz=in[2];
    return(GL_TRUE);
}

/* Geom */
typedef struct {
   double x, y, z;
} Point;

typedef struct {
   long p1, p2, p3;
} Triangle;

Point* points;
Point* image_points;
Triangle* triangles;
int nb_pts;
int nb_triangles;

void print_point(Point p)
{
    printf("%f %f %f\n", p.x, p.y, p.z);
}

void print_triangle(Triangle t)
{
    printf("%d %d %d\n", t.p1, t.p2, t.p3);
}

PyObject* list_from_triangle(Triangle t)
{
    PyObject* list = PyList_New(3);
    PyList_SetItem(list, 0, PyInt_FromLong( t.p1 ));
    PyList_SetItem(list, 1, PyInt_FromLong( t.p2 ));
    PyList_SetItem(list, 2, PyInt_FromLong( t.p3 ));

    return list;
}

static double max2(double a, double b)
{
    if (a > b) return a;
    else return b;
}

static double max3(double a, double b, double c)
{
    if (a > b) return max2(a, c);
    else return max2(b, c);
}

static PyObject *
project_all(PyObject *self, PyObject *args)
{
	PyObject *model;
	PyObject *proj;
	PyObject *view;

	if (!PyArg_ParseTuple(args, "OOO:project_all", &model, &proj, &view)) {
		return NULL;
	}

    GLdouble modelMatrix[16];
    GLdouble projMatrix[16];
    GLint viewport[4];

    int i;
    for (i = 0; i < PyList_Size(model); i++) {
        PyObject* x = PyList_GetItem(model, i);
        modelMatrix[i] = PyFloat_AsDouble(x);
    }
    for (i = 0; i < PyList_Size(proj); i++) {
        PyObject* x = PyList_GetItem(proj, i);
        projMatrix[i] = PyFloat_AsDouble(x);
    }
    for (i = 0; i < PyList_Size(view); i++) {
        PyObject* x = PyList_GetItem(view, i);
        viewport[i] = PyFloat_AsDouble(x);
    }

    /*
    for p in g.points:
        x, y, z = gluProject(p.pos[0], p.pos[1], p.pos[2], model, proj, view)
        image_points.append( (x,y,z) )
     */
    for (i = 0; i < nb_pts; i++) {
        Point p = points[i];
        Point ip;
        gluProject(p.x, p.y, p.z,
                      modelMatrix,
                      projMatrix,
                      viewport,
                      &ip.x, &ip.y, &ip.z);
        image_points[i] = ip;
    }

    return Py_None;
}

static int cross_product_2d(double Ux, double Uy, double Vx, double Vy) {
    // printf("%f %f %f %f\n", Ux, Uy, Vx, Vy);
    return Ux * Vy >= Uy * Vx;
}

static PyObject *
obj_hits(PyObject *self, PyObject *args)
{
    puts("obj_hits");
    long x_arg, y_arg;
	if (!PyArg_ParseTuple(args, "ll", &x_arg, &y_arg)) {
		return NULL;
	}
    printf("x %d y %d\n", x_arg, y_arg);

    double x = x_arg, y = y_arg;

    PyObject* hits = PyList_New(0);
    int i;
    for (i = 0; i < nb_triangles; i++) {
        Triangle t = triangles[i];

        int x1, x2, x3;
        int y1, y2, y3;
        int z1, z2, z3;

        Point p1 = image_points[t.p1];
        // print_point(p1);
        x1 = p1.x; y1 = p1.y; z1 = p1.z;

        Point p2 = image_points[t.p2];
        // print_point(p2);
        x2 = p2.x; y2 = p2.y; z2 = p2.z;

        Point p3 = image_points[t.p3];
        // print_point(p3);
        x3 = p3.x; y3 = p3.y; z3 = p3.z;

        int b1 = cross_product_2d(x - x1, y - y1, x - x2, y - y2);
        int b2 = cross_product_2d(x - x2, y - y2, x - x3, y - y3);
        int b3 = cross_product_2d(x - x3, y - y3, x - x1, y - y1);
        // printf("b1 b2 b3 %d %d %d\n", b1, b2, b3);
        
        if (b1 == b2 && b2 == b3) {
            puts("hit");
            PyObject* pair = PyList_New(2);
            PyList_SetItem(pair, 0, 
                            PyFloat_FromDouble( max3(z1, z2, z3) ));
            PyList_SetItem(pair, 1, list_from_triangle(t));

            PyList_Append(hits, pair);
        }
    }

    return hits;
}

static PyObject *
obj_setup(PyObject *self, PyObject *args)
{
	PyObject *py_points;
	PyObject *py_triangles;
	if (!PyArg_ParseTuple(args, "OO:read", &py_points, &py_triangles)) {
		return NULL;
	}

    nb_pts = PyList_Size(py_points);
    nb_triangles = PyList_Size(py_triangles);
    printf("Object: %d %d\n", nb_pts, nb_triangles);

    points       = (Point*)    malloc(nb_pts * sizeof(Point));
    image_points = (Point*)    malloc(nb_pts * sizeof(Point));
    triangles    = (Triangle*) malloc(nb_triangles * sizeof(Triangle));

    int i;
    /* points */
    for (i = 0; i < nb_pts; i++) {
        PyObject* py_p = PyList_GetItem(py_points, i);

        Point p; 
        p.x = PyFloat_AsDouble( PyList_GetItem(py_p, 0) );
        p.y = PyFloat_AsDouble( PyList_GetItem(py_p, 1) );
        p.z = PyFloat_AsDouble( PyList_GetItem(py_p, 2) );

        // print_point(p);
        points[i] = p;
    }

    /* triangles */
    for (i = 0; i < nb_triangles; i++) {
        PyObject* py_t = PyList_GetItem(py_triangles, i);

        Triangle t; 
        t.p1 = PyLong_AsLong( PyList_GetItem(py_t, 0) );
        t.p2 = PyLong_AsLong( PyList_GetItem(py_t, 1) );
        t.p3 = PyLong_AsLong( PyList_GetItem(py_t, 2) );

        triangles[i] = t;
    }

    return Py_None;
}

/* Module functions table. */

static PyMethodDef
module_functions[] = {
    { "read", obj_read, METH_VARARGS, "Compress a byte buffer." },
    { "setup", obj_setup, METH_VARARGS, "Set stuff" },
    { "projall", project_all, METH_VARARGS, "Project stuff" },
    { "gethits", obj_hits, METH_VARARGS, "Get number of hits" },
    { NULL }
};

/* This function is called to initialize the module.
 * The name of this function must be init<mymodule> (module name from setup.py)
 */
void
initcobj(void)
{
    setlocale(LC_NUMERIC, "C");    
    Py_InitModule3("cobj", module_functions, "Do stuff with geometry.");
}
