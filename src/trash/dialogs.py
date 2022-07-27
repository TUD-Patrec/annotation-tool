"""
Created on 30.11.2019

@author: Erik Altermann
@email: Erik.Altermann@tu-dortmund.de
"""

import json
import os

import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QIntValidator

#import global_variables as g


# from main import IO_Controller

class SaveClassesDialog(QtWidgets.QDialog):
    """Dialog displaying displaying an exlusive choise between all classes
    
    example code:
        dlg = saveClassesDialog(QWidget)
        result = dlg.exec_()
    the result will be an integer, see in the method pressedButtons
    
    """

    def __init__(self, parent: QtWidgets.QWidget, selected_class: int = None):
        """Initializes the dialog and sets up the gui
        
        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        selected_class : int (optional)
            Index of an already selected class, or None if 
            no class was selected before starting this dialog.
        ----------
            
        """
        super(SaveClassesDialog, self).__init__(parent)
        self.setWindowTitle("Save Class")

        self.classButtons = [QtWidgets.QRadioButton(text) for text in g.classes]

        self.layout = QtWidgets.QVBoxLayout()
        for button in self.classButtons:
            self.layout.addWidget(button)
            button.clicked.connect(lambda _: self.enable_ok_button())

        qbtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(lambda: self.done(self.pressed_button()))
        self.buttonBox.rejected.connect(lambda: self.done(-1))

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        if selected_class is not None:
            self.classButtons[selected_class].setChecked(True)
            self.enable_ok_button()

    def pressed_button(self) -> int:
        """Checks which radioButton is currently checked
        
        Returns:
        --------
        class_index : int
            index of the selected class.
            -1 if no class was selected
        --------
        """
        class_index = -1
        for i, button in enumerate(self.classButtons):
            if button.isChecked():
                class_index = i
        return class_index

    def enable_ok_button(self):
        """Enables the OkButton"""

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)


class SaveAttributesDialog(QtWidgets.QDialog):
    """Dialog displaying displaying a non-exlusive choice between all attributes
    
    example code:
        dlg = saveAttributesDialog(QWidget)
        _ = dlg.exec_()
        result = dlg.result()

    """

    def __init__(self, parent: QtWidgets.QWidget, selected_attr: list = None):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        selected_attr : list (optional)
            list of booleans with one value per attribute. 
            1 if an attribute is present. 0 if its not.
            argument is None if no attributes were selected before starting this dialog.
        ----------
            
        """
        super(SaveAttributesDialog, self).__init__(parent)
        self.setWindowTitle("Save Attributes")

        self.attributeButtons = [QtWidgets.QCheckBox(text) for text in g.attributes]

        self.layout = QtWidgets.QVBoxLayout()
        for button in self.attributeButtons:
            self.layout.addWidget(button)
        qbtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(lambda: self.done(1))
        self.buttonBox.rejected.connect(lambda: self.done(0))

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        if selected_attr is not None:
            for i, attr_val in enumerate(selected_attr):
                self.attributeButtons[i].setChecked(attr_val)

    def result(self) -> int:
        """Checks which buttons are currently checked
        
        Returns:
        --------
        attr_int : int
            the list of buttons gets transformed into a boolean list by checking their isChecked() state.
        --------
        """
        pressed_buttons = []
        for button in self.attributeButtons:
            pressed_buttons.append(button.isChecked() + 0)
        return pressed_buttons



class SaveAttributesDialogKitchen(QtWidgets.QDialog):
    """Dialog displaying displaying a non-exlusive choice between all attributes

    The attributes are separated into different groups

    example code:
        dlg = saveAttributesDialog(QWidget)
        _ = dlg.exec_()
        result = dlg.result()

    """

    def __init__(self, parent: QtWidgets.QWidget, groups: list, dependencies: dict = None, selected_attr: list = None):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        groups : list
            list containing lists of attribute indexes that belong to a group
        dependencies : dict
            dictionary keyed with attribute indexes. Each key give back a list of attribute indexes that may be used
        selected_attr : list (optional)
            list of booleans with one value per attribute.
            1 if an attribute is present. 0 if its not.
            argument is None if no attributes were selected before starting this dialog.
        ----------

        """
        super(SaveAttributesDialogKitchen, self).__init__(parent)
        self.setWindowTitle("Save Attributes")

        self.groups = groups
        self.dependencies = dependencies

        self.attributeButtons = [QtWidgets.QCheckBox(text) for text in g.attributes]
        self.setup_dependencies()

        v_layout = QtWidgets.QVBoxLayout()
        self.setLayout(v_layout)

        attribute_widget = QtWidgets.QWidget(None)
        v_layout.addWidget(attribute_widget)
        h_layout = QtWidgets.QHBoxLayout()
        attribute_widget.setLayout(h_layout)

        self.group_widgets = []

        for group in groups:
            scroll_area = QtWidgets.QScrollArea(None)
            widget = QtWidgets.QWidget(None)
            v_box = QtWidgets.QVBoxLayout()
            for attr in group:
                v_box.addWidget(self.attributeButtons[attr])

            widget.setLayout(v_box)
            scroll_area.setWidget(widget)
            h_layout.addWidget(scroll_area)

            self.group_widgets.append(widget)

        qbtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(lambda: self.done(1))
        self.buttonBox.rejected.connect(lambda: self.done(0))
        v_layout.addWidget(self.buttonBox)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        if selected_attr is not None:
            for i, attr_val in enumerate(selected_attr):
                self.attributeButtons[i].setChecked(attr_val)

    def setup_dependencies(self):
        for group in self.groups[1:]:
            for j in group:
                self.attributeButtons[j].setEnabled(False)
        for i, group in enumerate(self.groups):
            for j in group:
                self.attributeButtons[j].clicked.connect(lambda _, g=i, b=j: self.update_dependencies(g, b))

    def update_dependencies(self, group_id, button_id):
        print(group_id, button_id)
        # print(g.windows.dataset)
        for i in self.groups[group_id]:  # Modify buttons in same Group
            if i == button_id:
                continue
            elif g.windows.dataset == "Brownie":  # Consider exceptions because of doubled attributes
                if button_id in [34, 35] and i in [34, 35]:
                    continue
                elif button_id in [53, 54] and i in [53, 54]:
                    continue
            elif g.windows.dataset == "Eggs":
                if button_id in [27, 28] and i in [27, 28]:
                    continue
                elif button_id in [29, 30] and i in [29, 30]:
                    continue
            elif g.windows.dataset == "Sandwich":
                if button_id in [10, 11] and i in [10, 11]:
                    continue

            self.attributeButtons[i].setChecked(False)

        if group_id + 1 == len(self.groups):
            return  # If group_id is the last group there is no other group that is dependent on it

        for i, group in enumerate(self.groups[(group_id + 1):]):  # Modify buttons in next Groups
            # print(group)

            for j in group:
                button = self.attributeButtons[j]
                button.setEnabled(False)
                button.setChecked(False)
                button.setVisible(False)

        for i in self.groups[group_id]:  # Enable dependencies
            if self.attributeButtons[i].isChecked():
                for j in self.dependencies[i]:
                    button = self.attributeButtons[j]
                    button.setVisible(True)
                    button.setEnabled(True)

        for widget in self.group_widgets:
            widget.adjustSize()

        # Check if at least 1 attribute is checked.
        # Enable if true disable otherwise to prevent 0-vectors for attribute representation
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(any(self.result()))

    def result(self) -> list:
        """Checks which buttons are currently checked

        Returns:
        --------
        attr_int : int
            the list of buttons gets transformed into a boolean list by checking their isChecked() state.
        --------
        """
        pressed_buttons = []
        for button in self.attributeButtons:
            pressed_buttons.append(button.isChecked() + 0)
        # print(pressed_buttons)
        return pressed_buttons


class SettingsDialog(QtWidgets.QDialog):
    """Dialog displaying displaying all settings that are changeable by the user
    
    example code:
        changed_settings = []
        dlg = settingsDialog(QWidget,settings,changed_settings)
        _ = dlg.exec_()
    results are stored in the changed_settings parameter of the __init__ method
    """

    def __init__(self, parent: QtWidgets.QWidget):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        settings : dict
            all settings
        changed_settings : list
            list of tuples (key,value) for the settings dict.
            should be empty, it gets filled with changes in the accept method.
            
        ----------
        """

        super(SettingsDialog, self).__init__(parent)
        uic.loadUi(f'..{os.sep}ui{os.sep}settings.ui', self)
        # self.findChild(qtclass,name)

        # ----- Video Settings Widgets -----

        self.floorEnableButton = self.findChild(QtWidgets.QRadioButton, 'floorEnableRadioButton')
        self.floorDisableButton = self.findChild(QtWidgets.QRadioButton, 'floorDisableRadioButton')

        self.dynamicEnableButton = self.findChild(QtWidgets.QRadioButton, 'dynamicEnableRadioButton')
        self.dynamicDisableButton = self.findChild(QtWidgets.QRadioButton, 'dynamicDisableRadioButton')

        self.fastLineEdit = self.findChild(QtWidgets.QLineEdit, 'fastLineEdit')
        self.fastLineEdit.setValidator(QIntValidator(1, 1000))
        self.normalLineEdit = self.findChild(QtWidgets.QLineEdit, 'normalLineEdit')
        self.normalLineEdit.setValidator(QIntValidator(1, 1000))
        self.slowLineEdit = self.findChild(QtWidgets.QLineEdit, 'slowLineEdit')
        self.slowLineEdit.setValidator(QIntValidator(1, 1000))

        # ----- File Settings widgets -----

        self.annotatorLineEdit = self.findChild(QtWidgets.QLineEdit, 'annotatorLineEdit')
        self.annotatorLineEdit.setValidator(QIntValidator(0, 1000))

        self.unlabeledLineEdit = self.findChild(QtWidgets.QLineEdit, 'unlabeledLineEdit')
        self.labeledLineEdit = self.findChild(QtWidgets.QLineEdit, 'labeledLineEdit')
        self.stateLineEdit = self.findChild(QtWidgets.QLineEdit, 'stateLineEdit')
        self.backupLineEdit = self.findChild(QtWidgets.QLineEdit, 'backupLineEdit')

        self.unlabeledButton = self.findChild(QtWidgets.QPushButton, 'unlabeledButton')
        self.labeledButton = self.findChild(QtWidgets.QPushButton, 'labeledButton')
        self.stateButton = self.findChild(QtWidgets.QPushButton, 'stateButton')
        self.backupButton = self.findChild(QtWidgets.QPushButton, 'backupButton')

        # -----Get all settings-----

        if g.settings['floorGrid']:
            self.floorEnableButton.setChecked(True)
        else:
            self.floorDisableButton.setChecked(True)

        if g.settings['dynamicFloor']:
            self.dynamicEnableButton.setChecked(True)
        else:
            self.dynamicDisableButton.setChecked(True)

        self.fastLineEdit.setText(str(g.settings['fastSpeed']))
        self.normalLineEdit.setText(str(g.settings['normalSpeed']))
        self.slowLineEdit.setText(str(g.settings['slowSpeed']))

        self.annotatorLineEdit.setText(str(g.settings['annotator_id']))

        self.unlabeledLineEdit.setText(str(g.settings['openFilePath']))
        self.labeledLineEdit.setText(str(g.settings['saveFinishedPath']))
        self.stateLineEdit.setText(str(g.settings['stateFinishedPath']))
        self.backupLineEdit.setText(str(g.settings['backUpPath']))

        # -----Connecting signals and slots-----
        self.unlabeledButton.clicked.connect(lambda _: self.browse_dir('unlabeled'))
        self.labeledButton.clicked.connect(lambda _: self.browse_dir('labeled'))
        self.stateButton.clicked.connect(lambda _: self.browse_dir('states'))
        self.backupButton.clicked.connect(lambda _: self.browse_dir('backup'))

    def browse_dir(self, directory_type: str):
        """Open directory dialog and saves the chosen directory in the correct lineEdit
        
        Arguments:
        ----------
        directoryType : str
            Tells which lineEdit to fill with the new directory
        """

        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select a new Directory', '')
        if directory != '':
            if directory_type == 'unlabeled':
                self.unlabeledLineEdit.setText(directory)
            elif directory_type == 'labeled':
                self.labeledLineEdit.setText(directory)
            elif directory_type == 'states':
                self.stateLineEdit.setText(directory)
            elif directory_type == 'backup':
                self.backupLineEdit.setText(directory)

    def accept(self, *args, **kwargs):
        """Computes the result and saves it to changed_settings
        
        Overwritten method from QtWidgets.QDialog
        gets called when the dialog gets closed via the ok button and closes the dialog
        
        """

        g.settings['floorGrid'] = self.floorEnableButton.isChecked()
        g.settings['dynamicFloor'] = self.dynamicEnableButton.isChecked()

        int_line_edits = [self.fastLineEdit, self.normalLineEdit, self.slowLineEdit, self.annotatorLineEdit]
        int_setting = ['fastSpeed', 'normalSpeed', 'slowSpeed', 'annotator_id']

        for lineSetting, lineEdit in zip(int_setting, int_line_edits):
            if not lineEdit.text() == '':
                g.settings[lineSetting] = int(lineEdit.text())

        str_line_edits = [self.unlabeledLineEdit, self.labeledLineEdit, self.stateLineEdit, self.backupLineEdit]
        str_setting = ['openFilePath', 'saveFinishedPath', 'stateFinishedPath', 'backUpPath']

        for lineSetting, lineEdit in zip(str_setting, str_line_edits):
            g.settings[lineSetting] = lineEdit.text()

        with open(g.settings_path, 'w') as f:
            json.dump(g.settings, f)

        return QtWidgets.QDialog.accept(self)


class EnterIDDialog(QtWidgets.QDialog):
    """Dialog for entering the annotator_id and the number of annotations
    
    example code:
        dlg = enterIDDialog(QWidget,io_controller,0)
        result = dlg.exec_()
        
    result is a boolean that shows wether the annotator aborted or confirmed
    if confirmed the annotator_id and number of annotations are saved to the io_controller
    
    """

    def __init__(self, parent, io_controller, annotator_id):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        io_controller : main.IO_Controller
            io_controller of the application
        annotator_id : int
            sets the initial value of the annotatorIDLineEdit for faster confirmation
        ----------
        """
        super(EnterIDDialog, self).__init__(parent)
        self.setWindowTitle("Enter your ID and number of this attempt")
        self.io_controller = io_controller

        self.layout = QtWidgets.QGridLayout()

        self.layout.addWidget(QtWidgets.QLabel("Please fill out this information"), 0, 0, 1, 2)

        self.layout.addWidget(QtWidgets.QLabel("Annotator ID:"), 1, 0)
        self.layout.addWidget(QtWidgets.QLabel("Number of this annotation run:"), 3, 0)

        self.annotatorIDLineEdit = QtWidgets.QLineEdit(str(annotator_id))
        self.annotatorIDLineEdit.setValidator(QIntValidator(0, 1000))
        self.layout.addWidget(self.annotatorIDLineEdit, 1, 1)

        self.annotatorIDErrorLabel = QtWidgets.QLabel("")
        self.annotatorIDErrorLabel.setStyleSheet('color: red')
        self.layout.addWidget(self.annotatorIDErrorLabel, 2, 1)

        self.triesSpinBox = QtWidgets.QSpinBox()
        self.triesSpinBox.setMinimum(1)
        self.layout.addWidget(self.triesSpinBox, 3, 1)

        self.triesErrorLabel = QtWidgets.QLabel("")
        self.triesErrorLabel.setStyleSheet('color: red')
        self.layout.addWidget(self.triesErrorLabel, 4, 1)

        qbtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(lambda: self.save_inputs())
        self.buttonBox.rejected.connect(lambda: self.reject())

        self.layout.addWidget(self.buttonBox, 5, 0, 1, 2)
        self.setLayout(self.layout)

    def save_inputs(self):
        """Saves the annotator_id and closes the dialog returning true
        
        """
        annotator_id = self.annotatorIDLineEdit.text()
        tries = self.triesSpinBox.value()

        if (annotator_id != '') and (tries != ''):
            self.io_controller.save_id(annotator_id, tries)
            self.accept()
        else:
            if annotator_id == '':
                self.annotatorIDErrorLabel.setText("This field is required")
            if tries == '':
                self.triesErrorLabel.setText("This field is required")


class ProgressDialog(QtWidgets.QDialog):
    """Displays 2 Progressbars. The first for the progress of a single step. The second for progress of steps.
    
    example code:
        dlg = changeLabelsDialog(QWidget)
        _ = dlg.exec_()
    
    anytime the user changes a label it gets saved automatically 
    """

    def __init__(self, parent: QtWidgets.QWidget, process_name: str, num_steps: int):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        process_name : str
            
        num_steps : int
        
        ----------
        """
        super(ProgressDialog, self).__init__(parent)
        uic.loadUi(f'..{os.sep}ui{os.sep}progressbar.ui', self)

        # self.findChild(qtclass,name)

        self.process_label = self.findChild(QtWidgets.QLabel, 'process_label')
        self.process_label.setText(process_name)

        self.step_label = self.findChild(QtWidgets.QLabel, 'step_label')

        self.step_progressBar = self.findChild(QtWidgets.QProgressBar, 'progressBar')

        self.steps_progressBar = self.findChild(QtWidgets.QProgressBar, 'progressBar_2')
        self.steps_progressBar.setMaximum(num_steps)

    def advance_step(self, value):
        current_value = self.step_progressBar.value() + value
        self.step_progressBar.setValue(current_value)

    def set_step(self, value):
        self.step_progressBar.setValue(value)

    def advance_steps(self, value):
        current_value = self.steps_progressBar.value() + value
        self.steps_progressBar.setValue(current_value)
        if current_value >= self.steps_progressBar.maximum():
            self.done(0)

    def new_step(self, step_name: str, max_value: int):
        self.step_progressBar.setValue(0)
        self.step_progressBar.setMaximum(max_value)
        self.advance_steps(1)

        self.step_label.setText(step_name)


class OpenFileDialog(QtWidgets.QDialog):
    """Dialog to select a new File to open.
    
    example code:
        dlg = open_file_dialog(QWidget)
        result = dlg.exec_()
    
    anytime the user changes a label it gets saved automatically 
    """

    def __init__(self, parent: QtWidgets.QWidget):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        data : data_management.DataProcessor
        ----------
        """
        super(OpenFileDialog, self).__init__(parent)
        uic.loadUi(f'..{os.sep}ui{os.sep}openfile.ui', self)

        self.load_backup = False
        self.result = None

        browse_button = self.findChild(QtWidgets.QPushButton, "browse_button")
        browse_button.clicked.connect(lambda _: self.browse())

        self.path_lineEdit = self.findChild(QtWidgets.QLineEdit, "path_lineEdit")
        self.path_lineEdit.textChanged.connect(self.check_path)

        self.backup_button = self.findChild(QtWidgets.QRadioButton, 'backup_radioButton')
        self.backup_button.clicked.connect(lambda _: self.set_load_backup(True))
        self.scratch_button = self.findChild(QtWidgets.QRadioButton, 'scratch_radioButton')
        self.scratch_button.clicked.connect(lambda _: self.set_load_backup(False))

        self.new_button = self.findChild(QtWidgets.QRadioButton, "new_radioButton")
        self.new_button.clicked.connect(lambda _: self.scratch_button.setText("Start from Scratch"))
        self.new_button.clicked.connect(lambda _: self.backup_button.setText("Load Backup"))

        self.annotated_button = self.findChild(QtWidgets.QRadioButton, "annotated_radioButton")
        self.annotated_button.clicked.connect(lambda _: self.scratch_button.setText("Load original labels"))
        self.annotated_button.clicked.connect(lambda _: self.backup_button.setText("Load modified labels"))

        self.states_button = self.findChild(QtWidgets.QRadioButton, "states_radioButton")
        self.states_button.clicked.connect(lambda _: self.scratch_button.setText("Start from Scratch"))
        self.states_button.clicked.connect(lambda _: self.backup_button.setText("Load Backup"))

        self.kitchen_button = self.findChild(QtWidgets.QRadioButton, "kitchen_radioButton")

        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, 'buttonBox')
        self.ok_button = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)

    def set_load_backup(self, load):
        self.load_backup = load

    def browse(self):

        if self.new_button.isChecked():
            directory = g.settings['openFilePath']
            message = 'Select an unlabeled .csv file'
            filter_ = 'CSV Files (*.csv)'
        elif self.annotated_button.isChecked() or self.states_button.isChecked():
            directory = g.settings['saveFinishedPath']
            message = 'Select an _norm_data.csv file'
            filter_ = 'CSV Files (*norm_data.csv)'
        else:  # elif self.kitchen_button.isChecked():
            directory = g.settings['openFilePath']
            message = 'Select an _norm_data.csv file'
            filter_ = 'ZIP Files (*Video.zip)'

        file, _ = QtWidgets.QFileDialog.getOpenFileName(self, message, directory, filter_, '')

        if file != '':
            self.path_lineEdit.setText(file)

    def check_path(self, new_path):

        file_name = os.path.split(new_path)[1]

        name_fragments = file_name.split('.')[0].split('_')
        raw_data_name = name_fragments[0]
        for fragment in name_fragments[1:3]:
            # for fragment in name_fragments[1:]:
            raw_data_name += "_" + fragment
        file_name = raw_data_name

        backup_path = f'{g.settings["backUpPath"]}{os.sep}{file_name}_backup.txt'

        self.ok_button.setEnabled(os.path.exists(new_path))

        if os.path.exists(backup_path):
            self.backup_button.setEnabled(True)
            self.scratch_button.setEnabled(True)
            self.load_backup = self.backup_button.isChecked()
        else:
            self.backup_button.setEnabled(False)
            self.scratch_button.setEnabled(False)
            self.load_backup = False

    def accept(self, *args, **kwargs):
        if self.new_button.isChecked():
            annotated = 0
        elif self.annotated_button.isChecked():
            annotated = 1
        elif self.states_button.isChecked():
            annotated = 2
        else:  # elif self.kitchen_button.isChecked():
            annotated = 3
        path = self.path_lineEdit.text()

        self.result = (path, annotated, self.load_backup)

        return QtWidgets.QDialog.accept(self)


class PlotDialog(QtWidgets.QWidget):
    """
    example code:
        dlg = Plot_Dialog(QWidget)
        _ = dlg.exec_()
    
    """

    def __init__(self, parent: QtWidgets.QWidget = None, number_of_graphs=1):
        """Initializes the dialog and sets up the gui

        Arguments:
        ----------
        parent : QWidget
            parent widget of this dialog
        ----------
        """

        super(PlotDialog, self).__init__(parent)
        # uic.loadUi(f'..{os.sep}ui{os.sep}plotwindow.ui', self)
        self.number_of_graphs = number_of_graphs
        self.graphs = []
        vbox = QtWidgets.QVBoxLayout()
        for i in range(self.number_of_graphs):
            self.graphs.append(pg.PlotWidget(self))
            vbox.addWidget(self.graphs[i])
        self.setLayout(vbox)
        self.graph = self.graphs[0]

    def graph_widget(self):
        return self.graph

    def graph_widgets(self):
        return self.graphs
