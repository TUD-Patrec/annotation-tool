from enum import Enum

from PyQt6.QtGui import QKeySequence

from annotation_tool.annotation.modes import AnnotationMode


class AnnotationActions(Enum):
    COPY = 0
    PASTE = 1
    DELETE = 2
    UNDO = 3
    REDO = 4
    ANNOTATE = 5
    RESET = 6
    CUT = 7
    CUT_AND_ANNOTATE = 8
    MERGE_LEFT = 9
    MERGE_RIGHT = 10
    ACCEPT = 11
    REJECT = 12
    ACCEPT_ALL = 13
    MODIFY = 14
    CHANGE_FILTER = 15
    JUMP_PREVIOUS = 16
    JUMP_NEXT = 17


class ReplayActions(Enum):
    PLAY_OR_PAUSE = 0
    TOGGLE_FORWARD_BACKWARD = 1
    INCREASE_SPEED = 2
    DECREASE_SPEED = 3
    SKIP_FRAMES = 4
    SKIP_FRAMES_BACK = 5
    SKIP_FRAMES_FAR = 6
    SKIP_FRAMES_BACK_FAR = 7


ActionToShortcut = {
    AnnotationActions.COPY: QKeySequence.StandardKey.Copy,
    AnnotationActions.PASTE: QKeySequence.StandardKey.Paste,
    AnnotationActions.DELETE: QKeySequence.StandardKey.Delete,
    AnnotationActions.UNDO: QKeySequence.StandardKey.Undo,
    AnnotationActions.REDO: QKeySequence.StandardKey.Redo,
    AnnotationActions.ANNOTATE: QKeySequence("A"),
    AnnotationActions.CUT: QKeySequence("C"),
    AnnotationActions.CUT_AND_ANNOTATE: QKeySequence("X"),
    AnnotationActions.MERGE_LEFT: QKeySequence("L"),
    AnnotationActions.MERGE_RIGHT: QKeySequence("R"),
    AnnotationActions.ACCEPT: QKeySequence("A"),
    AnnotationActions.REJECT: QKeySequence("R"),
    AnnotationActions.MODIFY: QKeySequence("M"),
    AnnotationActions.CHANGE_FILTER: QKeySequence(""),
    AnnotationActions.JUMP_PREVIOUS: QKeySequence("Ctrl+Left"),
    AnnotationActions.JUMP_NEXT: QKeySequence("Ctrl+Right"),
    AnnotationActions.RESET: QKeySequence("Ctrl+R"),
    ReplayActions.PLAY_OR_PAUSE: QKeySequence("Space"),
    ReplayActions.TOGGLE_FORWARD_BACKWARD: QKeySequence("B"),
    ReplayActions.SKIP_FRAMES: QKeySequence("Right"),
    ReplayActions.SKIP_FRAMES_BACK: QKeySequence("Left"),
    ReplayActions.SKIP_FRAMES_FAR: QKeySequence("Shift+Right"),
    ReplayActions.SKIP_FRAMES_BACK_FAR: QKeySequence("Shift+Left"),
}


def get_shortcut(action):
    return ActionToShortcut[action] if action in ActionToShortcut else None


def get_annotation_actions(mode: AnnotationMode):
    if mode == AnnotationMode.MANUAL:
        return [
            AnnotationActions.ANNOTATE,
            AnnotationActions.CUT,
            AnnotationActions.CUT_AND_ANNOTATE,
            AnnotationActions.MERGE_LEFT,
            AnnotationActions.MERGE_RIGHT,
        ]
    elif mode == AnnotationMode.RETRIEVAL:
        return [
            AnnotationActions.ACCEPT,
            AnnotationActions.REJECT,
            # AnnotationActions.ACCEPT_ALL, TODO: implement
            AnnotationActions.MODIFY,
            AnnotationActions.CHANGE_FILTER,
        ]
    else:
        return []


def get_edit_actions(mode: AnnotationMode):
    if mode == AnnotationMode.MANUAL:
        return [
            AnnotationActions.COPY,
            AnnotationActions.PASTE,
            AnnotationActions.DELETE,
            AnnotationActions.RESET,
            AnnotationActions.UNDO,
            AnnotationActions.REDO,
        ]
    elif mode == AnnotationMode.RETRIEVAL:
        return []
    else:
        return []


def get_replay_actions(mode: AnnotationMode):
    if mode == AnnotationMode.MANUAL:
        return [
            ReplayActions.PLAY_OR_PAUSE,
            # ReplayActions.TOGGLE_FORWARD_BACKWARD,  # TODO: implement
            ReplayActions.SKIP_FRAMES,
            ReplayActions.SKIP_FRAMES_BACK,
            ReplayActions.SKIP_FRAMES_FAR,
            ReplayActions.SKIP_FRAMES_BACK_FAR,
            AnnotationActions.JUMP_PREVIOUS,
            AnnotationActions.JUMP_NEXT,
        ]
    elif mode == AnnotationMode.RETRIEVAL:
        return [
            ReplayActions.PLAY_OR_PAUSE,
            ReplayActions.TOGGLE_FORWARD_BACKWARD,
            ReplayActions.SKIP_FRAMES,
            ReplayActions.SKIP_FRAMES_BACK,
            ReplayActions.SKIP_FRAMES_FAR,
            ReplayActions.SKIP_FRAMES_BACK_FAR,
        ]
    else:
        return []
