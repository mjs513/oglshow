all: view
view:
	llvm-g++ -Werror -g -O2 -framework GLUT -framework OpenGL -framework Cocoa glut_viewer.cpp -o glut_viewer

test:
	llvm-g++ -m32 -Werror -g -O2 -framework GLUT -framework OpenGL -framework Cocoa main.cpp -o unittest
