import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

class VideoContextMenu(qtw.QDialog):
    settings_changed = qtc.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(VideoContextMenu, self).__init__(*args, **kwargs)
        
        self.form = qtw.QFormLayout(self)
        
        self.add_video = qtw.QPushButton(self)
        self.form.addRow()






if __name__ == "__main__":
    import sys
    app = qtw.QApplication(sys.argv)
    MainWindow = VideoContextMenu('C:')
    MainWindow.show()
    sys.exit(app.exec_())