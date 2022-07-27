import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

class GUI(qtw.QMainWindow):
    path_to_data = qtc.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)

        self.resize(1350, 900)
        self.setMinimumSize(1350, 900)
        self.setWindowTitle('Annotation Tool')
        #self.setWindowIcon()

        self.presentation_plane = qtw.QStackedWidget(self)
        self.setCentralWidget(self.presentation_plane)      
        
        # Menu Bar
        self._make_menu_bar()
    
        # left dock-widget
        self.left_dock = qtw.QDockWidget('')
        left_area = qtc.Qt.LeftDockWidgetArea
        self.left_dock.setAllowedAreas(left_area)
        self.left_dock.setFeatures(qtw.QDockWidget.NoDockWidgetFeatures)
        self.left_dock.setWidget(qtw.QWidget())
        self.addDockWidget(left_area, self.left_dock)

        # lower dock-widget
        self.bottom_dock = qtw.QDockWidget('')
        bottom_area = qtc.Qt.BottomDockWidgetArea
        self.bottom_dock.setAllowedAreas(bottom_area)
        self.bottom_dock.setFeatures(qtw.QDockWidget.NoDockWidgetFeatures)
        self.bottom_dock.setWidget(qtw.QWidget())
        self.addDockWidget(bottom_area, self.bottom_dock)


        # right dock-widget
        self.right_dock = qtw.QDockWidget('')
        right_area = qtc.Qt.RightDockWidgetArea
        self.right_dock.setAllowedAreas(right_area)
        self.right_dock.setFeatures(qtw.QDockWidget.NoDockWidgetFeatures)
        self.right_dock.setWidget(qtw.QWidget())
        self.addDockWidget(right_area, self.right_dock)


        # showing Main-Frame
        self.show()


    def _make_menu_bar(self):
        menu = self.menuBar()

        file_menu = menu.addMenu('File')
        open_act = file_menu.addAction('Open')
        #qtg.QFileDialog.getOpenFileName(self, 'OpenFile')
        open_act.triggered.connect(self.open)
        save_act = file_menu.addAction('Save')
        edit_menu = menu.addMenu('Edit')
        settings_menu = menu.addMenu('Options')
        annotation_menu = menu.addMenu('Annotation_Mode')
        display_menu = menu.addMenu('Display')
        help_menu = menu.addMenu('Help')
    

    def open(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='Video like (*.mp4 *.avi)')
        self.path_to_data.emit(filename)