import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import sys, logging, logging.config

from .data_classes.annotation import Annotation
from .annotation_widget import QAnnotationWidget
from .gui import GUI
from .playback import PlayWidget
from .display_current_sample import QDisplaySample
from .data_classes.singletons import Settings
from .utility.functions import FrameTimeMapper
from .utility import filehandler
from .utility.breeze_resources import *

from .media import QMediaWidget

class MainApplication(qtw.QApplication):
    update_media_pos = qtc.pyqtSignal(int)
    update_annotation_pos = qtc.pyqtSignal(int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Controll-Attributes
        self.annotation = None
        self.position = None
        self.n_frames = None 
        
        # Main Window
        self.gui = GUI()
                
        self.annotation_widget = QAnnotationWidget()
        self.player = PlayWidget()
        self.media_player = QMediaWidget()
        self.display_sample = QDisplaySample()
        
        self.gui.set_left_widget(self.player)
        self.gui.set_central_widget(self.media_player)
        self.gui.set_right_widget(self.display_sample)
        self.gui.set_bottom_widget(self.annotation_widget)

        # CONNECTIONS
        # from player
        self.player.playing.connect(self.media_player.play)
        self.player.paused.connect(self.media_player.pause)
        self.player.skip_frames.connect(self.skip_frames)
        self.player.replay_speed_changed.connect(self.media_player.setReplaySpeed)

        # from media_player
        self.media_player.positionChanged.connect(lambda x: self.update_position(x, update_media=False, update_annotation=True))
        self.media_player.cleanedUp.connect(self.gui.cleaned_up)
        
        # from annotation_widget
        self.annotation_widget.samples_changed.connect(lambda x,y: self.display_sample.set_selected(y))
        self.annotation_widget.position_changed.connect(lambda x: self.update_position(x, update_media=True, update_annotation=False))
        self.annotation_widget.interrupt_replay.connect(self.media_player.pause)
        self.annotation_widget.interrupt_replay.connect(self.player.pause)
        self.annotation_widget.update_label.connect(self.player.update_label)
        
        # from GUI
        self.gui.save_pressed.connect(self.save_annotation)
        self.gui.load_annotation.connect(self.load_annotation)
        self.gui.skip_frames.connect(self.skip_frames)
        self.gui.annotate_pressed.connect(lambda : self.annotation_widget.annotate_btn.trigger())
        self.gui.merge_left_pressed.connect(lambda : self.annotation_widget.merge_left_btn.trigger())
        self.gui.merge_right_pressed.connect(lambda : self.annotation_widget.merge_right_btn.trigger())
        self.gui.cut_pressed.connect(lambda: self.annotation_widget.cut_btn.trigger())
        self.gui.cut_and_annotate_pressed.connect(lambda: self.annotation_widget.cut_and_annotate_btn.trigger())
        self.gui.play_pause_pressed.connect(lambda : self.player.play_stop_button.trigger())
        self.gui.decrease_speed_pressed.connect(self.player.decrease_speed)
        self.gui.increase_speed_pressed.connect(self.player.increase_speed)
        self.gui.undo_pressed.connect(self.annotation_widget.undo)
        self.gui.redo_pressed.connect(self.annotation_widget.redo)
        self.gui.settings_changed.connect(self.settings_changed)
        self.gui.settings_changed.connect(self.media_player.settingsChanges)
        self.gui.exit_pressed.connect(self.media_player.shutdown)
        
        # from main_controller
        self.update_annotation_pos.connect(self.annotation_widget.set_position)
        self.update_media_pos.connect(self.media_player.setPosition)
    
    def skip_frames(self, forward_step, fast):
        if self.annotation:
            settings = Settings.instance()
            n = settings.big_skip if fast else settings.small_skip
            if not forward_step:
                n *= -1
            
            new_pos = max(0, min(self.n_frames - 1, self.position + n))
            self.update_position(new_pos, True, False)
                    
    def update_position(self, new_pos, update_media, update_annotation):
        assert 0 <= new_pos < self.n_frames
        self.position = new_pos
        
        if update_annotation:
            self.update_annotation_pos.emit(self.position)
        if update_media:
            self.update_media_pos.emit(self.position)
    
    @qtc.pyqtSlot(Annotation)
    def load_annotation(self, annotation):
        FrameTimeMapper.instance().set_annotation(annotation.frames, annotation.duration)
        
        self.annotation = annotation
        self.n_frames = annotation.frames
                
        # load video
        self.media_player.loadAnnotation(self.annotation)
        self.display_sample.set_annotation(self.annotation)
        self.annotation_widget.set_annotation(self.annotation)
        self.annotation_widget.set_position(0)
        self.player.reset()
        self.update_position(0, True, True)
        self.save_annotation()
    
    def save_annotation(self):
        if self.annotation is None:
            logging.info('Nothing to save - annotation-object is None')
        else:
            logging.info('Saving current state')
            samples = self.annotation_widget.samples
            self.annotation.samples = samples
            for idx, x in enumerate(self.annotation.samples):
                logging.info('{}-Sample: ({}, {})'.format(idx, x.start_position, x.end_position))
            self.annotation.to_disk()

    @qtc.pyqtSlot()
    def settings_changed(self):
        settings = Settings.instance()
        app = qtw.QApplication.instance()
        
        custom_font = qtg.QFont()
        custom_font.setPointSize(settings.font);
        app.setFont(custom_font)
        
        FrameTimeMapper.instance().settings_changed()
        
        log_config_dict = filehandler.logging_config()
        log_config_dict['handlers']['screen_handler']['level'] = 'DEBUG' if settings.debugging_mode else 'WARNING'
        logging.config.dictConfig(log_config_dict)
        
        self.annotation_widget.settings_changed()
                
        toggle_stylesheet(settings.darkmode)
        

def toggle_stylesheet(darkmode):
    '''
    Toggle the stylesheet to use the desired path in the Qt resource
    system (prefixed by `:/`) or generically (a path to a file on
    system).

    :path:      A full path to a resource or file on system
    '''

    # get the QApplication instance,  or crash if not set
    app = qtw.QApplication.instance()
    if app is None:
        raise RuntimeError("No Qt Application found.")

    file = qtc.QFile(":/dark/stylesheet.qss") if darkmode else qtc.QFile(":/light/stylesheet.qss")
    file.open(qtc.QFile.ReadOnly | qtc.QFile.Text)
    stream = qtc.QTextStream(file)
    app.setStyleSheet(stream.readAll())
           
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

def main():
    sys.excepthook = except_hook
    
    app = MainApplication(sys.argv)
    app.setStyle("Fusion")    
        
    settings = Settings.instance()
    custom_font = qtg.QFont()
    custom_font.setPointSize(settings.font);
    app.setFont(custom_font)
    
    file = qtc.QFile(":/dark/stylesheet.qss") if settings.darkmode else qtc.QFile(":/light/stylesheet.qss")
    file.open(qtc.QFile.ReadOnly | qtc.QFile.Text)
    stream = qtc.QTextStream(file)
    app.setStyleSheet(stream.readAll())
        
    sys.exit(app.exec_())
