#!/usr/bin/env python

"""PyQt4 port of the opengl/hellogl example from Qt v4.x"""

'''
Debug note
----------

It you see the following message when debuging with pdb:

    Flood message: "QCoreApplication::exec: The event loop is already running"

Use this pyqt call before:

    from PyQt4 import QtCore, QtGui, QtOpenGL
    set_trace()
'''

import sys
import math
from PyQt4 import QtCore, QtGui, QtOpenGL
from os.path import expanduser, dirname, splitext, join

QtCore.pyqtRemoveInputHook()

try:
    from OpenGL import GL
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "OpenGL hellogl",
                            "PyOpenGL must be installed to run this example.",
                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
                            QtGui.QMessageBox.NoButton)
    sys.exit(1)

APP_NAME = "Python Qt obj Viewer"

class Window(QtGui.QMainWindow):
    ''' Same container than C++ '''
    def __init__(self, verbose = 0):
        QtGui.QMainWindow.__init__(self, None)
        self.verbose = verbose

        self.glWidget = GLWidget()
        self.setCentralWidget(self.glWidget)
        self.setWindowTitle(self.tr(APP_NAME))
        self.loadSettings()

        # Model tree
        self.mtDisabled = True
        if not self.mtDisabled:
            self.createDockWindows()
            self.connect(self.hideAllButton, QtCore.SIGNAL("pressed()"), self.hideAll)
            self.connect(self.showAllButton, QtCore.SIGNAL("pressed()"), self.showAll)
            self.connect(self.objList, QtCore.SIGNAL("itemChanged(QListWidgetItem*)"),
                    self.mtItemActivated)

        # This help to keep the focus and be able to close the app with Echap
        self.setFocus()

    def keyPressEvent(self, event):
        ''' (DEBUG) This is a good place to put actions '''
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        if event.key() == QtCore.Qt.Key_O:
            self.loadFile()
        if event.key() == QtCore.Qt.Key_W: # Close file
            sdk.show_wireframe = not sdk.show_wireframe
            self.glWidget.updateGL()
        if event.key() == QtCore.Qt.Key_H: # highlight triangle under cursor
            sdk.highlight = not sdk.highlight
            # print dir(QtCore.Qt)
            if event.modifiers() == QtCore.Qt.ShiftModifier:
                sdk.highlight_implementation = "Python"
            elif event.modifiers() == QtCore.Qt.AltModifier:
                sdk.highlight_implementation = "CPython"
            else:
                sdk.highlight_implementation = "octree"
                sdk.setup_octree()
                sdk.draw_octree = False

            self.glWidget.setMouseTracking(sdk.highlight)
        if event.key() == QtCore.Qt.Key_G: # Grid
            print 'cacasd'
            sdk.grid = not sdk.grid
            self.glWidget.updateGL()
        if event.key() == QtCore.Qt.Key_C: # Conference
            sdk.start_conference_as_slave_twisted()

    def loadFile(self):
        settings = QtCore.QSettings("Oglshow", APP_NAME)
        dn = settings.value("last_dirname").toString()
        if not dn:
            dn = expanduser('~') # $HOME dir or My Documents

        fn = QtGui.QFileDialog.getOpenFileName(None, 
                "Open File", dn,
                "Wavefront 3D Files (*.obj)")
        if fn:
            # Use str(fn) to convert a QString to a python string
            pystr_fn = str(fn)
            last_dirname = dirname(pystr_fn)
            settings.setValue("last_dirname", QtCore.QVariant(last_dirname))

            self.sdkLoadFile([pystr_fn, self.verbose])

    def sdkLoadFile(self, options):
        self.glWidget.loadFile(options)
        self.updateModelTree()

    def closeEvent(self, event):
        self.saveSettings()

    def saveSettings(self):
        ''' Saving window's geometry '''
        settings = QtCore.QSettings("pyview", APP_NAME)

        # Restoring window's geometry
        settings.setValue("pos", QtCore.QVariant(self.pos()))
        settings.setValue("size", QtCore.QVariant(self.size()))

        settings.setValue("size", QtCore.QVariant(self.size()))

    def loadSettings(self):
        ''' Restoring window's geometry '''
        settings = QtCore.QSettings("pyview", APP_NAME)

        # FIXME: Those default are not good, use the one from the wxWidgets viewer
        pos = settings.value("pos", QtCore.QVariant(QtCore.QPoint(200, 200))).toPoint()
        size = settings.value("size", QtCore.QVariant(QtCore.QSize(400, 400))).toSize()
        self.resize(size);
        self.move(pos);

    ###
    #  Model tree
    ###
    def showAll(self): self.showOrHideAll(hide = False)
    def hideAll(self): self.showOrHideAll(hide = True)

    def showOrHideAll(self, hide): 
        self.mtDisabled = True
        if hide:
            state = QtCore.Qt.Unchecked
            sdk.hide_all()
        else:
            state = QtCore.Qt.Checked
            sdk.show_all()

        for i,name in enumerate(sdk.scene.part_names):
            self.objList.item(i).setCheckState(state)

        self.glWidget.updateGL()
        self.mtDisabled = False

    def mtItemActivated(self, item):
        if not self.mtDisabled:
            i = self.objList.row(item)
            checked = item.checkState() == QtCore.Qt.Checked
            sdk.show_obj(i, checked)
            self.glWidget.updateGL()

    def updateModelTree(self):
        if not self.mtDisabled:
            L = self.objList 
            L.clear()

            for i,name in enumerate(sdk.scene.part_names):
                L.addItem(name)
                L.item(i).setCheckState(QtCore.Qt.Checked)

    def createDockWindows(self):
        dock = QtGui.QDockWidget("Model tree", self)

        self.objList = QtGui.QListWidget(dock)

        self.showAllButton = QtGui.QPushButton("Show all")
        self.hideAllButton = QtGui.QPushButton("Hide all")

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.showAllButton)
        buttonLayout.addWidget(self.hideAllButton)
        
        mainLayout =  QtGui.QVBoxLayout()
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(self.objList)

        modelTreeDialog = QtGui.QDialog()
        modelTreeDialog.setLayout(mainLayout)

        dock.setWidget(modelTreeDialog)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)


class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.setAutoBufferSwap(False)

    def minimumSizeHint(self):
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        return QtCore.QSize(sdk.w, sdk.h)

    def initializeGL(self):
        pass

    def loadFile(self, params):
        ''' Weird stuff happens at init, resizeGL (and sdk.reshape called twice
        the second time with 0, 0
        '''
        sdk.load_file(*params) # which is file name
        print self.size()
        size = self.size()
        self.resizeGL(size.width(), size.height())
        self.updateGL()

    def paintGL(self):
        sdk.render()

    def resizeGL(self, width, height):
        self.width = width
        self.height = height
        sdk.reshape(width, height)

    def mousePressEvent(self, event):
        self.pressed = True

        x = event.pos().x()
        y = event.pos().y()
        sdk.mouse_start = [x, y]

    def mouseReleaseEvent(self, event):
        self.pressed = False

    def mouseMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()

        if self.pressed:
            manip_mode = 'rotate'
            if event.buttons() & QtCore.Qt.LeftButton and \
                event.buttons() & QtCore.Qt.RightButton:
                manip_mode = 'pan'

            if [x,y] != sdk.mouse_start:
                sdk.pointer_move(manip_mode,
                        sdk.mouse_start[0], sdk.mouse_start[1], x, y)
                self.updateGL()

            sdk.mouse_start = [x, y]
        else:
            if sdk.highlight:
                sdk.highlight_cursor = [x, self.height - y]
                self.updateGL() # dont call update twice if we are manipulating too

    def wheelEvent(self, event):
        direction = 1 if event.delta() > 0 else -1
        sdk.pointer_move('zoom',
            0, 0, direction * 100, direction * 100);

        self.updateGL()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    from scene import ArgsOptions
    ao = ArgsOptions()

    window = Window(ao.options.verbose)

    # Set files
    options = [ao.options.fn,
               ao.options.verbose]

    # Window dimensions
    w, h = 250, 250

    from viewer import OglSdk
    sdk = OglSdk(w, h, window.glWidget.swapBuffers)
    window.sdkLoadFile(options)

    # Start display
    window.show()
    sys.exit(app.exec_())
