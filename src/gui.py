import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import os
import logging

from .data_classes.singletons import Paths, Settings
from .data_classes.annotation import Annotation
import numpy as np
from .util import util
from .data_classes.datasets import DatasetDescription
from .dialogs.settings import SettingsDialog
from .adaptive_scroll_area import QAdaptiveScrollArea
import shutil

paths: Paths = Paths.instance()

class GUI(qtw.QMainWindow):
    load_annotation = qtc.pyqtSignal(Annotation)
    save_pressed = qtc.pyqtSignal()
    exit_pressed = qtc.pyqtSignal()
    play_pause_pressed = qtc.pyqtSignal()
    skip_frames = qtc.pyqtSignal(bool, bool)
    cut_pressed = qtc.pyqtSignal()
    cut_and_annotate_pressed = qtc.pyqtSignal()
    merge_left_pressed = qtc.pyqtSignal()
    merge_right_pressed = qtc.pyqtSignal()
    annotate_pressed = qtc.pyqtSignal()
    increase_speed_pressed = qtc.pyqtSignal()
    decrease_speed_pressed = qtc.pyqtSignal()
    reset_pressed = qtc.pyqtSignal()
    undo_pressed = qtc.pyqtSignal()
    redo_pressed = qtc.pyqtSignal()
    merge_adjacent_pressed = qtc.pyqtSignal()
    settings_changed = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)
        
        # window setup
        settings = Settings.instance()
        x_min, y_min, x_max, y_max = settings.window_extrema()
        self.setMinimumSize(x_min, y_min)
        
        self.resize(settings.window_x, settings.window_y)
        logging.info(self.size())
        self.setWindowTitle('Annotation Tool')
        #self.setWindowIcon()

        self.main_widget = qtw.QWidget()
        self.vbox = qtw.QVBoxLayout()
        self.hbox = qtw.QHBoxLayout()
        self.main_widget.setLayout(self.vbox)
        
        self.left_widget = qtw.QWidget()
        self.bottom_widget = qtw.QWidget()
        self.right_widget = qtw.QWidget()
        self.central_widget = qtw.QWidget()
        
        self.hbox.addWidget(self.left_widget, alignment=qtc.Qt.AlignLeft)
        self.hbox.addWidget(self.central_widget, stretch=1)
        self.hbox.addWidget(self.right_widget, alignment=qtc.Qt.AlignRight)
        
        self.vbox.addLayout(self.hbox, stretch=1)
        self.vbox.addWidget(self.bottom_widget)
        
        self.setCentralWidget(self.main_widget)
        
        # Menu Bar
        self.make_menu_bar()
        
        self.statusBar().show()
        
        # showing Main-Frame
        self.show()
    
    def write_to_statusbar(self, txt):
        self.statusBar().showMessage(str(txt))
    
    def make_menu_bar(self):               
        self.file_menu()
        self.video_menu()
        self.edit_menu()
        self.settings_menu()
    
    def video_menu(self):
        menu = self.menuBar()
        video_menu = menu.addMenu('&Video')
        
        video_menu.addAction(
            'Play/Pause',
            self.play_pause_pressed,
            qtg.QKeySequence(qtc.Qt.Key_Space)
        )
        
        video_menu.addAction(
            'Next Frame',
            lambda : self.skip_frames.emit(True, False),
            qtg.QKeySequence(qtc.Qt.Key_Right)
        )
        
        video_menu.addAction(
            'Last Frame',
            lambda : self.skip_frames.emit(False, False),
            qtg.QKeySequence(qtc.Qt.Key_Left)
        )
        
        video_menu.addAction(
            'Skip +100 Frames',
            lambda : self.skip_frames.emit(True, True),
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_Right)
        )
        
        video_menu.addAction(
            'Skip -100 Frames',
            lambda : self.skip_frames.emit(False, True),
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_Left)
        )
        
        video_menu.addAction(
            'Increase replay speed',
            lambda : self.increase_speed_pressed.emit()
        )
        
        video_menu.addAction(
            'Decrease replay speed',
            lambda : self.decrease_speed_pressed.emit()
        )
            
    def edit_menu(self):
        menu = self.menuBar()
        edit_menu = menu.addMenu('&Edit')
                 
        edit_menu.addAction(
            'Annotate',
            self.annotate_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_A)
        ) 
                
        edit_menu.addAction(
            'Cut',
            self.cut_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_C)
        )
        
        edit_menu.addAction(
            'Cut + Annotate',
            self.cut_and_annotate_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_X)
        )
        
        edit_menu.addAction(
            'Merge Left',
            self.merge_left_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_L)
        )
        
        edit_menu.addAction(
            'Merge Right',
            self.merge_right_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_R)
        )
        
        edit_menu.addAction(
            'Merge adjacent annotations',
            self.merge_adjacent_pressed
        )
                
        
        edit_menu.addAction(
            'Reset Annotation',
            self.reset_pressed,
        )
        
        edit_menu.addAction(
            'Undo',
            self.undo_pressed,
            qtg.QKeySequence.Undo
        )
        
        edit_menu.addAction(
            'Redo',
            self.redo_pressed,
            qtg.QKeySequence.Redo
        )
    
    def settings_menu(self):
        menu = self.menuBar()
        settings_menu = menu.addMenu('&Options')
        settings_menu.addAction(
            'Options',
            self.open_settings,
        )
        settings_menu.addAction(
            'Help',
        )
    
    def file_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu('&File')
        file_menu.addAction(
                'New',
                self.create_new_annotation,
                qtg.QKeySequence.New
            )
            
        file_menu.addAction(
            'Open',
            self.load_existing_annotation,
            qtg.QKeySequence.Open
        )
        
        file_menu.addAction(
            'Save',
            self.save_pressed,
            qtg.QKeySequence.Save
        )
        
        file_menu.addAction(
            'List Annotations',
        )
        
        file_menu.addAction(
            'Export Annotation',
            self.export_annotation,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_E)
        )
        
        #file_menu.addAction(
        #    'Import Annotation',
        #    ,
        #    qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_I)
        #)
        
        file_menu.addAction(
            'Edit Datasets',
            self.edit_datasets
        )
        
        file_menu.addAction(
            'Exit',
            self._exit, 
            qtg.QKeySequence.Close
        )    
    
    def open_settings(self):
        self.dialog = SettingsDialog()
        self.dialog.settings_changed.connect(self.settings_changed)
        self.dialog.open()
    
    def create_new_annotation(self):
        self.dialog = QNewAnnotationDialog()
        self.dialog.load_annotation.connect(self.load_annotation)
        self.dialog.open()    
    
    def load_existing_annotation(self):
        self.dialog = QLoadExistingAnnotationDialog()
        self.dialog.load_annotation.connect(self.load_annotation)
        self.dialog.open()
    
    def export_annotation(self):
        self.dialog = QExportAnnotationDialog()
        # self.dialog.existing_annotation.connect(self.open_existing_annotation)
        self.dialog.open()
    
    def edit_datasets(self):
        self.dialog = QEditDatasets()
        self.dialog.open()
        pass
    
    def set_left_widget(self, widget):
        self.hbox.replaceWidget(self.left_widget, widget)
        self.left_widget.setParent(None)
        self.left_widget = widget
    
    def set_central_widget(self, widget):
        self.hbox.replaceWidget(self.central_widget, widget)
        self.central_widget.setParent(None)
        self.central_widget = widget
        self.central_widget.adjustSize()
            
    def set_right_widget(self, widget):
        self.hbox.replaceWidget(self.right_widget, widget)
        self.right_widget.setParent(None)
        self.right_widget = widget
        
    def set_bottom_widget(self, widget):
        self.vbox.replaceWidget(self.bottom_widget, widget)
        self.bottom_widget.setParent(None)
        self.bottom_widget = widget
    
    def _exit(self):
        self.exit_pressed.emit()
        self.close()
 

class QNewAnnotationDialog(qtw.QDialog):
    load_annotation = qtc.pyqtSignal(Annotation)
    
    def __init__(self, *args, **kwargs):
        super(QNewAnnotationDialog, self).__init__(*args, **kwargs)
                
        form = qtw.QFormLayout()
        self.annotation_name = qtw.QLineEdit()
        self.annotation_name.setPlaceholderText('Insert name here.')
        self.annotation_name.textChanged.connect(lambda _: self.check_enabled())
        form.addRow('Annotation name:', self.annotation_name)
                
        self.datasets = get_datasets()
        self.combobox = qtw.QComboBox()
        for data_description in self.datasets:
            self.combobox.addItem(data_description.name)
    
        self.combobox.currentIndexChanged.connect(lambda _: self.check_enabled())
        
        form.addRow('Datasets:', self.combobox)
                
        self.line_edit = QLineEditAdapted()
        self.line_edit.setPlaceholderText('No File selected.')
        self.line_edit.setReadOnly(True)
        self.line_edit.textChanged.connect(lambda _: self.check_enabled())
        self.line_edit.mousePressed.connect(lambda: self.select_input_source())
        
        form.addRow('Input File:', self.line_edit)
                        
        self.try_using_experimental_media_player = qtw.QCheckBox()
        form.addRow('Try experimental media-player:', self.try_using_experimental_media_player)
        
        self.open_button = qtw.QPushButton()
        self.open_button.setText('Open')
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(lambda _: self.open_pressed())
        
        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText('Cancel')
        self.cancel_button.clicked.connect(lambda _: self.cancel_pressed())
        
        self.button_widget = qtw.QWidget()
        self.button_widget.setLayout(qtw.QHBoxLayout())
        self.button_widget.layout().addWidget(self.open_button)
        self.button_widget.layout().addWidget(self.cancel_button)
        
    
        form.addRow(self.button_widget)
        self.setLayout(form)
        self.setMinimumWidth(500)
        
    def select_input_source(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='Video MoCap (*.mp4 *.avi *.csv)')
        if util.is_non_zero_file(filename):
            self.line_edit.setText(filename)
            
    def check_enabled(self):
        enabled = True
        if self.annotation_name.text() == '':
            enabled = False
        if self.combobox.count() == 0:
            enabled = False
        if not(os.path.isfile(self.line_edit.text())):
            enabled = False
        self.open_button.setEnabled(enabled)
    
    def cancel_pressed(self):
        self.close()
        
    def open_pressed(self):
        self.check_enabled()
        if self.open_button.isEnabled():
            idx = self.combobox.currentIndex()
            use_media_player = self.try_using_experimental_media_player.isChecked()
            
            dataset_description = self.datasets[idx]
            
            annotator_id = Settings.instance().annotator_id
            annotation = Annotation(annotator_id, dataset_description, self.annotation_name.text(), self.line_edit.text(), use_media_player)
            self.load_annotation.emit(annotation)
            self.close()

   
class QLoadExistingAnnotationDialog(qtw.QDialog):
    load_annotation = qtc.pyqtSignal(Annotation)
    
    def __init__(self, *args, **kwargs):
        super(QLoadExistingAnnotationDialog, self).__init__(*args, **kwargs)
        form = qtw.QFormLayout()
        self.combobox = qtw.QComboBox()
        
        self.annotations = get_annotations()
        for annotation in self.annotations:
            self.combobox.addItem(annotation.name)
                
        self.combobox.currentIndexChanged.connect(lambda x: self.process_combobox_value(x))
        
        form.addRow('Annotation_Name:', self.combobox)
                
        self.line_edit = QLineEditAdapted()
        self.line_edit.setPlaceholderText('No associated Input-File found.')
        self.line_edit.setReadOnly(True)
        self.line_edit.textChanged.connect(lambda _: self.check_enabled())
        self.line_edit.mousePressed.connect(lambda: self.select_input_source())
        
        form.addRow('Input File:', self.line_edit)
        
        self.dataset_line_edit = qtw.QLineEdit()
        self.dataset_line_edit.setPlaceholderText('No associated Dataset found.')
        self.dataset_line_edit.setReadOnly(True)
        
        form.addRow('Dataset Path:', self.dataset_line_edit)
        
        self.open_button = qtw.QPushButton()
        self.open_button.setText('Open')
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(lambda _: self.open_pressed())
        
        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText('Cancel')
        self.cancel_button.clicked.connect(lambda _: self.cancel_pressed())
        
        self.button_widget = qtw.QWidget()
        self.button_widget.setLayout(qtw.QHBoxLayout())
        self.button_widget.layout().addWidget(self.open_button)
        self.button_widget.layout().addWidget(self.cancel_button)
        
    
        form.addRow(self.button_widget)
        self.setLayout(form)
        self.setMinimumWidth(500)
        
        self.process_combobox_value(self.combobox.currentIndex())
    
    def process_combobox_value(self, idx):
        if idx >= 0:   
            annotation = self.annotations[idx]

            dataset = annotation.dataset
            self.dataset_line_edit.setText(dataset.name)
            
            
            if os.path.isfile(annotation.input_file):
                hash = util.footprint_of_file(annotation.input_file)
                if annotation.footprint == hash:
                    self.line_edit.setText(annotation.input_file) 
                else:
                    self.line_edit.setText('The path of the input has changed, please select the new path.')
            else:
                self.line_edit.setText('The path of the input has changed, please select the new path.')
        self.check_enabled()

    def select_input_source(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='Video MoCap (*.mp4 *.avi *.csv)')
        if util.is_non_zero_file(file_path):
            hash = util.footprint_of_file(file_path)
            idx = self.combobox.currentIndex()
            
            if idx < 0:
                self.line_edit.setText('')
                return
            
            annotation = self.annotations[idx]
            other_hash = annotation.footprint
                
            if hash == other_hash:
                self.line_edit.setText(file_path)
            else:
                self.line_edit.setText('The input_file is not compatible with the selected annotation, please select the correct file.')
        self.check_enabled()
    
    def check_enabled(self):
        if self.combobox.count() == 0:
            self.open_button.setEnabled(False)
        elif not(os.path.isfile(self.line_edit.text())):
            self.open_button.setEnabled(False)
        elif self.combobox.currentIndex() < 0:
            self.open_button.setEnabled(False)
        elif not util.is_non_zero_file(self.annotations[self.combobox.currentIndex()].dataset.path):
            self.open_button.setEnabled(False)
        else:
            self.open_button.setEnabled(True)
    
    def cancel_pressed(self):
        self.close()
        
    def open_pressed(self):
        idx = self.combobox.currentIndex()
        annotation = self.annotations[idx]
        
        annotation.input_file = self.line_edit.text()
        
        self.load_annotation.emit(annotation)
        self.close()
   
        
class QExportAnnotationDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super(QExportAnnotationDialog, self).__init__(*args, **kwargs)
        form = qtw.QFormLayout()
        self.annotation_combobox = qtw.QComboBox()
    
        self.annotations = get_annotations()
        for annotation in self.annotations:
            self.annotation_combobox.addItem(annotation.name)
        
        self.annotation_combobox.currentIndexChanged.connect(lambda _: self.check_enabled())
        form.addRow('Annotation Name:', self.annotation_combobox)
        
        self.naming_combobox = qtw.QComboBox()
        self.naming_combobox.addItem('default')
        
        self.export_path_line_edit = QLineEditAdapted()
        self.export_path_line_edit.setPlaceholderText('No Directory selected.')
        self.export_path_line_edit.setReadOnly(True)
        self.export_path_line_edit.mousePressed.connect(self.get_path)
        self.export_path_line_edit.textChanged.connect(lambda _: self.check_enabled())
        form.addRow('Export Directory:', self.export_path_line_edit)
        
        
        self.export_annotated_file = qtw.QCheckBox()
        form.addRow('Add Copy of annotated File:', self.export_annotated_file)
        
        self.export_scheme = qtw.QCheckBox()
        form.addRow('Add dataset-scheme:', self.export_scheme)
        
        self.export_dependencies = qtw.QCheckBox()
        form.addRow('Add dataset-dependencies:', self.export_dependencies)
        
        self.export_meta_informations = qtw.QCheckBox()
        form.addRow('Add meta-informations:', self.export_meta_informations)
        
        self.zip_exportation = qtw.QCheckBox()
        form.addRow('Compress files into ZIP-archive:', self.zip_exportation)
        
        self.open_button = qtw.QPushButton()
        self.open_button.setText('Open')
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(lambda _: self.open_pressed())
        
        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText('Cancel')
        self.cancel_button.clicked.connect(lambda _: self.cancel_pressed())
        
        self.button_widget = qtw.QWidget()
        self.button_widget.setLayout(qtw.QHBoxLayout())
        self.button_widget.layout().addWidget(self.open_button)
        self.button_widget.layout().addWidget(self.cancel_button)
        form.addRow(self.button_widget)
        
        self.setLayout(form)
        self.setMinimumWidth(400)
        
    def get_path(self):
        path = qtw.QFileDialog.getExistingDirectory(self, directory='')
        if os.path.isdir(path):
            self.export_path_line_edit.setText(path)
    
    def check_enabled(self):
        enabled = True
        
        idx = self.annotation_combobox.currentIndex()
        if idx == -1:
            enabled = False
        
        if not(os.path.isdir(self.export_path_line_edit.text())):
            enabled = False
        
        self.open_button.setEnabled(enabled)
    
    def cancel_pressed(self):
        self.close()
        
    def open_pressed(self):
        dir_path = self.export_path_line_edit.text()
        idx = self.annotation_combobox.currentIndex()
        
        # Grab informations from annotation.pkl
        annotation = self.annotations[idx]
        annotated_file = annotation.input_file
        input_filename = os.path.split(annotated_file)[1]
        annotator_id = annotation.annotator_id
        
        # Create directory for exportation
        folder = os.path.join(dir_path, 'annotation_{}_by_{}'.format(annotation.name, annotator_id))
        if os.path.isdir(folder):
            logging.warning('ALREADY EXISTING: {}'.format(folder))
        exportation_directory = util.create_dir(folder)
        del folder
        
        # Export main annotation-file
        array = annotation.to_numpy()
        util.numpy_to_csv(os.path.join(exportation_directory, 'annotation.csv'), array)
        logging.info('{} created.'.format('annotation.csv'))
                
        # Export copy of the annotated file
        if self.export_annotated_file.isChecked():
            out_path = os.path.join(exportation_directory, input_filename)
            logging.info('Copying {} -> {}'.format(annotated_file, out_path))
            shutil.copy2(annotated_file, out_path)
            logging.info('Copying succesfull.')
            del out_path
        
        # Export dataset-scheme
        if self.export_scheme.isChecked():
            logging.info('Exporting dataset-scheme.')
            out_path = os.path.join(exportation_directory, 'scheme.json')
            dataset_scheme = annotation.dataset.scheme
            util.write_json(data=dataset_scheme, path=out_path)       
            del out_path
        
        # Export dataset-dependencies
        if self.export_dependencies.isChecked():
            logging.info('Exporting dataset-dependencies.')
            out_path = os.path.join(exportation_directory, 'dependencies.csv')
            data = np.array(annotation.dataset.dependencies)
            util.numpy_to_csv(path=out_path, data=data)
            del out_path
            del data

        # Export meta-informations        
        if self.export_meta_informations.isChecked():
            logging.info('Exporting meta-informations')
            meta_dict = dict()
            meta_dict['name'] = annotation.name
            meta_dict['dataset_name'] = annotation.dataset.name
            meta_dict['annotator_id'] = annotation.annotator_id
            meta_dict['input_file'] = annotation.input_file
            meta_dict['footprint'] = annotation.footprint
            meta_dict['last_edited'] = str(annotation.last_edited)
            
            out_path = os.path.join(exportation_directory, 'meta_informations.json')
            util.write_json(path=out_path, data=meta_dict)
            del meta_dict
            del out_path
        
        # Compress Folder to ZIP
        if self.zip_exportation.isChecked():
            logging.info('CREATING ZIP-Archive.')
            out_path = os.path.join(dir_path, 'annotation_{}_by_{}'.format(annotation.name, annotator_id))
            shutil.make_archive(out_path, 'zip', exportation_directory)
            shutil.rmtree(exportation_directory)
            logging.info('ZIP-File created.')
        
        self.close()


class QEditDatasets(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super(QEditDatasets, self).__init__(*args, **kwargs)
        vbox = qtw.QVBoxLayout()
        
        self.scroll_widget = QAdaptiveScrollArea(self)
        self.scroll_widget.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        
        vbox.addWidget(self.make_header())
        vbox.addWidget(self.scroll_widget, stretch=1)       
        
        self.bottom_widget = qtw.QWidget()
        self.bottom_widget.setLayout(qtw.QFormLayout())
        
        self._name = qtw.QLineEdit()
        self._name.setPlaceholderText('NoName')
        self.bottom_widget.layout().addRow('Name', self._name)
        
        self._scheme = QLineEditAdapted()
        self._scheme.setPlaceholderText('Path to dataset scheme.')
        self._scheme.setReadOnly(True)
        self._scheme.mousePressed.connect(self.get_scheme_path)
        self.bottom_widget.layout().addRow('Scheme', self._scheme)

        self._dependencies = QLineEditAdapted()
        self._dependencies.setPlaceholderText('Path to dataset dependencies.')
        self._dependencies.setReadOnly(True)
        self._dependencies.mousePressed.connect(self.get_dependencies_path)
        self.bottom_widget.layout().addRow('Dependencies', self._dependencies)
        
        self.add_button = qtw.QPushButton('Add')
        self.add_button.setFixedWidth(100)
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(lambda _: self.add_pressed())
        self.bottom_widget.layout().addRow(self.add_button)
        
        vbox.addWidget(self.bottom_widget) 
        
        self.setLayout(vbox)
        self.setMinimumSize(600,400)
        
        self._reload()

    def get_scheme_path(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='(*.json)')
        if util.is_non_zero_file(file_path):
            # TODO Checking input file if a valid scheme
            
            self.add_button.setEnabled(True)
            self._scheme.setText(file_path)
        else:
            self.add_button.setEnabled(False)
            self._scheme.setText('')
        
    def get_dependencies_path(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='(*.csv)')
        if util.is_non_zero_file(file_path):
            # check dependencies valid
            self._dependencies.setText(file_path)
        else:
            self._dependencies.setText('')
    
    def make_header(self):
        row_widget = qtw.QWidget(self)
        hbox = qtw.QHBoxLayout(row_widget)
        row_widget.setLayout(hbox)
                
        id_lbl = qtw.QLabel('ID')
        id_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(id_lbl)
        
        name_lbl = qtw.QLabel('Name')
        name_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(name_lbl)
        
        dependencies_lbl = qtw.QLabel('Dependencies')
        dependencies_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(dependencies_lbl)

        modify_lbl = qtw.QLabel('Modify')
        modify_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(modify_lbl)
        
        remove_lbl = qtw.QLabel('Remove')
        remove_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(remove_lbl)
        
        return row_widget
    
    def _make_row(self, id):
        row_widget = qtw.QWidget(self)
        hbox = qtw.QHBoxLayout(row_widget)
        
        dataset = get_datasets()[id]
        
        idx_label = qtw.QLabel(str(id + 1))
        idx_label.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(idx_label)
        
        name_label =  qtw.QLabel(dataset.name)
        name_label.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(name_label)
                
        dependencies_exist = dataset.dependencies_exist
        dependencies_exist = 'loaded' if dependencies_exist else 'not loaded'
        dependencies_label = qtw.QLabel(dependencies_exist)
        dependencies_label.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(dependencies_label)
        
        edit_btn = qtw.QPushButton()
        edit_btn.setText('Edit')
        edit_btn.setEnabled(False)
        hbox.addWidget(edit_btn)
        
        remove_btn = qtw.QPushButton()
        remove_btn.setText('Remove')
        remove_btn.setEnabled(False)
        hbox.addWidget(remove_btn)
        
        row_widget.setLayout(hbox)
        
        return row_widget

    def _reload(self):
        self.scroll_widget.clear()
               
        for idx, _ in enumerate(get_datasets()):
            row = self._make_row(idx)
            row.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
            self.scroll_widget.addItem(row)
     
    def add_pressed(self):
        # TODO Check scheme and dependencies fit together
        name = self._name.text()
        if name == '':
            name = 'nameless'
        scheme_loaded = True
        try:
            N = 0
            scheme = util.read_json(self._scheme.text())
            for x, y in scheme:
                if type(x) != str:
                    scheme_loaded = False
                if type(y) != list:
                    scheme_loaded = False
                for elem in y:
                    if type(elem) != str:
                        scheme_loaded = False
                    N += 1
        except:
            scheme_loaded = False
        
        if not scheme_loaded:
            self._scheme.setText('Could not load scheme.') 
            return       
        
        if self._dependencies.text() != '':
            try:
                dependencies = util.csv_to_numpy(self._dependencies.text(), dtype=int)
            except:
                self._dependencies.setText('Could not load dependencies.')
                return
            if dependencies.shape[0] < 0 or dependencies.shape[1] != N:
                self._dependencies.setText('Could not load dependencies.')
                return
        else:
            dependencies = []
        
        dataset = DatasetDescription(name, scheme, dependencies)
        dataset.to_disk()
        
        self._reload()
        
        self._name.setText('')
        self._scheme.setText('')
        self._dependencies.setText('')
        self.add_button.setEnabled(False)


class QLineEditAdapted(qtw.QLineEdit):
    mousePressed = qtc.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(QLineEditAdapted, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.mousePressed.emit()



def get_datasets():
        datasets = []
        for file in os.listdir(paths.datasets):
                file_path = os.path.join(paths.datasets, file)
                if util.is_non_zero_file(file_path):
                    data_description = DatasetDescription.from_disk(file_path)
                    datasets.append(data_description)
        datasets.sort(key=lambda x: x.name)
        return datasets


def get_annotations():
    annotations = []
    for file in os.listdir(paths.annotations):
            file_path = os.path.join(paths.annotations, file)
            if util.is_non_zero_file(file_path):
                annotation = Annotation.from_disk(file_path)
                annotations.append(annotation)
    annotations.sort(key=lambda x: x.name)
    return annotations

 
if __name__ == "__main__":
    import sys
    app = qtw.QApplication(sys.argv)
    #MainWindow = GUI()
    MainWindow = QExportAnnotationDialog('C:')
    MainWindow.show()
    sys.exit(app.exec_())