import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from ..data_classes.singletons import Settings

class SettingsDialog(qtw.QDialog):
    settings_changed = qtc.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)
        form = qtw.QFormLayout()
        
        self.annotator_id = qtw.QLineEdit()
        form.addRow('Annotator_ID:', self.annotator_id)
        
        self.language = qtw.QComboBox()
        self.language.addItem('english')
        form.addRow('Language:', self.language)
        
        self.window_x = qtw.QLineEdit()
        form.addRow('Preferred Window_Width:', self.window_x)
        
        self.window_y = qtw.QLineEdit()
        form.addRow('Preferred Window_Height:', self.window_y)
        
        self.darkmode = qtw.QCheckBox()
        form.addRow('Darkmode:', self.darkmode)
        
        self.mocap_grid = qtw.QCheckBox()
        form.addRow('Mocap_Grid:', self.mocap_grid)
        
        self.frame_based = qtw.QCheckBox()
        form.addRow('Show Frame-Numbers:', self.frame_based)
        
        self.small_skip = qtw.QSlider(qtc.Qt.Horizontal)
        self.small_skip_display = qtw.QLabel()
        small_skip_widget = qtw.QWidget()
        small_skip_widget.setLayout(qtw.QHBoxLayout())
        small_skip_widget.layout().addWidget(self.small_skip, stretch=1)
        small_skip_widget.layout().addWidget(self.small_skip_display)
        form.addRow('Distance small step:', small_skip_widget)
        
        self.big_skip = qtw.QSlider(qtc.Qt.Horizontal)
        self.big_skip_display = qtw.QLabel()
        big_skip_widget = qtw.QWidget()
        big_skip_widget.setLayout(qtw.QHBoxLayout())
        big_skip_widget.layout().addWidget(self.big_skip, stretch=1)
        big_skip_widget.layout().addWidget(self.big_skip_display)
        form.addRow('Distance big step:', big_skip_widget)
        
        self.debugging_mode = qtw.QCheckBox()
        form.addRow('Debugging-Mode', self.debugging_mode)
        
        self.save_button = qtw.QPushButton()
        self.save_button.setText('Save')
        self.save_button.clicked.connect(lambda _: self.save_pressed())
        
        self.reset_button = qtw.QPushButton()
        self.reset_button.setText('Reset to Default')
        self.reset_button.clicked.connect(lambda _: self.reset_pressed())
        
        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText('Cancel')
        self.cancel_button.clicked.connect(lambda _: self.cancel_pressed())
        
        self.button_widget = qtw.QWidget()
        self.button_widget.setLayout(qtw.QHBoxLayout())
        self.button_widget.layout().addWidget(self.save_button)
        self.button_widget.layout().addWidget(self.reset_button)
        self.button_widget.layout().addWidget(self.cancel_button)
        
        
        
        form.addRow(self.button_widget)
        form.setAlignment(qtc.Qt.AlignCenter)
        
        self.setLayout(form)
        self.load_layout()
            
    def load_layout(self):
        settings = Settings.instance()
        x_min, y_min, x_max, y_max = settings.window_extrema()     
        
        id_validator = qtg.QIntValidator(self)
        self.annotator_id.setText(str(settings.annotator_id))
        self.annotator_id.setValidator(id_validator)
        self.annotator_id.setPlaceholderText(str(0))
        
        self.language.setCurrentIndex(settings.language)
        
        x_validator = qtg.QIntValidator(x_min, x_max, self)
        self.window_x.setValidator(x_validator)
        self.window_x.setText(str(settings.window_x))
        self.window_x.setPlaceholderText(str(settings.window_x))
        
        y_validator = qtg.QIntValidator(y_min, y_max, self)
        self.window_y.setValidator(y_validator)
        self.window_y.setText(str(settings.window_y))
        self.window_y.setPlaceholderText(str(settings.window_y))
        
        self.darkmode.setChecked(settings.darkmode)
        self.mocap_grid.setChecked(settings.mocap_grid)
        self.frame_based.setChecked(not settings.show_millisecs)
        
        self.small_skip.setRange(1, 10)
        self.small_skip.setTickInterval(1)
        self.small_skip.setSingleStep(1)
        self.small_skip.setTickPosition(qtw.QSlider.TicksBelow)
        self.small_skip.setValue(settings.small_skip)
        self.small_skip.valueChanged.connect(lambda x: self.small_skip_display.setText('{} [frames]'.format(x)))
        self.small_skip_display.setText('{} [frames]'.format(settings.small_skip))
        self.small_skip_display.setAlignment(qtc.Qt.AlignRight)
        self.small_skip_display.setFixedWidth(75)
        
        self.debugging_mode.setChecked(settings.debugging_mode)
        
        self.big_skip.setRange(50, 500)
        self.big_skip.setTickInterval(50)
        self.big_skip.setSingleStep(50)
        self.big_skip.setTickPosition(qtw.QSlider.TicksBelow)
        self.big_skip.setValue(settings.big_skip)
        self.big_skip.valueChanged.connect(lambda x: self.big_skip_display.setText('{} [frames]'.format(x)))
        self.big_skip_display.setText('{} [frames]'.format(settings.big_skip))
        self.big_skip_display.setAlignment(qtc.Qt.AlignRight)
        self.big_skip_display.setFixedWidth(75)
       
    def save_pressed(self):
        settings = Settings.instance()
        settings.annotation_id = int(self.annotator_id.text())
        settings.language = self.language.currentIndex()
        settings.debugging_mode = self.debugging_mode.isChecked()
        settings.window_x = int(self.window_x.text())
        settings.window_y = int(self.window_y.text())
        settings.darkmode = self.darkmode.isChecked()
        settings.mocap_grid = self.mocap_grid.isChecked()
        settings.show_millisecs = not self.frame_based.isChecked()
        settings.small_skip = self.small_skip.value()
        settings.big_skip = self.big_skip.value()
        
        
        settings.to_disk()
        self.settings_changed.emit()
        self.close()
     
    def reset_pressed(self):
        settings = Settings.instance()
        settings.reset()
        self.load_layout()
        
    def cancel_pressed(self):
        self.close()
 
if __name__ == "__main__":
    import sys
    app = qtw.QApplication(sys.argv)
    #MainWindow = GUI()
    MainWindow = SettingsDialog('C:')
    MainWindow.show()
    sys.exit(app.exec_())