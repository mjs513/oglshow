all: view
view:
	llvm-g++ -m32 -Werror -g -framework GLUT -framework OpenGL -framework Cocoa glew.c glut_viewer.cpp -o glut_viewer

test:
	llvm-g++ -m32 -Werror -g -O2 -framework GLUT -framework OpenGL -framework Cocoa glew.c main.cpp -o unittest
