#include "scene.h"
#include "view.h"

int test1() {
    Scene sc = load("../../py/test/data/gears.obj");
    sc.print();
    sc.bb.print();
    printf("%f\n", sc.bb.sphere_beam());
    print_vert( sc.bb.center());

    sc.compute_normals();
    sc.view.reset(sc.bb);
    sc.view.print();
}
        
void test2() {
    OglSdk sdk;
    sdk.w = 600;
    sdk.h = 480;

    sdk.load_file("../../py/test/data/gears.obj");
    sdk.scene.view.print();

    sdk.pointer_move("rotate", 100, 120, 110, 130);
    puts("");
    sdk.scene.view.print();
}

int test3() {
    // Scene sc = load("../../py/test/data/bigguy_00.obj");
    // Scene sc = load("../../py/test/data/gears.obj");
    Scene sc = load("../../py/test/data/bunny_normals.obj");
    sc.print();
}

extern int vert_sort(const void* _a, const void* _b) {
    vertex* a = (vertex*)_a;
    vertex* b = (vertex*)_b;
    if (a->z < b->z) return -1;
    else if (a->z > b->z) return 1;
    return 0;
}

int test4() {
    Scene sc = load("../../py/test/data/bunny_normals.obj");

    vertex* verts_copy = new vertex[sc.verts.size()];
    for (size_t i = 0; i < sc.verts.size(); ++i) {
        verts_copy[i] = sc.verts[i];
    }
    qsort(verts_copy, sc.verts.size(), sizeof(vertex), vert_sort);
    for (size_t i = 0; i < sc.verts.size(); ++i) {
        print_vert(verts_copy[i]);
    }
}

int test5() {
    // Scene sc = load("../../py/test/data/blade.obj");
    Scene sc = load("../../py/test/data/lucy.obj");
    puts("loaded");
    Chrono c;
    sc.compute_normals();
    printf("compute normals: "); c.get();
}

int test6() {
    Chrono c;

    vector<face> faces(28 * 1e6);
    vector<vertex> verts(14 * 1e6);

    vertex* triangle_normals = new vertex[faces.size()];
    vector<int>* vert_faces = new vector<int>[verts.size()];
    vector<vertex> normals;
    normals.resize(3 * faces.size());
    vector<face> faces_normals;
    faces_normals.resize(faces.size());

    printf("Alloc: "); c.get();
}

int main() {
    test5();
    return 0;
}
