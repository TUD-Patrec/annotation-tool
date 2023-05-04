# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). See also [RELEASE.md](RELEASE.md) for additional explanation.

## 0.8.3 (2023-05-04)

### 🐛 Fixes

- Fix filter for outdated timeouts (#33)

## 0.8.2 (2023-04-21)

### 🐛 Fixes

- Fix media position not always at 0 after reloading (#25)
- Fix mocap reader not always using the mocap-cache (#26)
- Fix some media loading bugs (#27)
- Fix some bugs and improve media-backend's FPS handling (#28)
- Fix media-readers used to access video-data (#31)

### 🧹 Refactoring

- Reimplement media-reading and media-playing (#24)
- Refactor synchronization-timer in the media-backend (#30)
- Fix media-readers used to access video-data (#31)

### 🏎️ Performance

- Reimplement media-reading and media-playing (#24)
- Fix mocap reader not always using the mocap-cache (#26)

## 0.8.1 (2023-03-17)

### 🐛 Fixes

- Fix/video player (#21)

## 0.8.0 (2023-03-16)

### ❗️ Breaking Changes

- Remodel file cache and rename class attributes (#10)

### 🚀 Features

- Add support for loading annotation-files (#16)
- Feat/UI changes (#17)

### 🐛 Fixes

- fix(local_files.py):  fixed bugs in local_files-dialog (#15)

### 📔 Documentation

- Update developer information (#2)
- Update README with additional pip installation instructions (#4)
- Update package homepage URL (#7)

### 🧹 Refactoring

- Rename some GUI items (#9)

### ⚙️ CI/CD

- Create workflow for automatic releases (#3)
- Fix script for detecting SemVer increments (#5)
- Add missing config for changelog generator (#6)
- Fix order of steps in release workflow (#8)
- Minor updates to the workflow files (#11)
- Fix repository not checked out on workflow call on lint.yml (#18)

### Other

- Update icon and name in title bar (#12)
- Add iconset for pyinstaller binaries (#13)
- Add Windows icon and add Mac build targets to Makefile (#14)

## 0.7.1 (2023-02-17)

### 🐛 Fix

- Create `__application_path__` if not existing (#1)

## 0.7.0 (2023-02-16)

### 🚀 Feature

- **settings**: Update settings, now stored as a json-file on disk
- **playback.py**: Updated slider to always move in 5%-steps
- **media**: Unstable implementation of multi-video reloading
- **data_model**: Implemented deepcopy for all dataclasses
- **manual_annotation**: Changed merge behaviour
- **main.py**: Upgrade to PyQt6

### 🐛 Fix

- **manual-annotation-controller**: Cut function fixed
- **new_annotation_dialog**: Changed order of elements, name now gets parsed from input-path
- **media_controller**: Fixed loading of outdated media
- **pyproject.toml**: Fixed packages
- **globalstate.py**: Deleting globalstate works again
- **annotation_list.py**: Fixed namespace error
- **histogram**: Fixed background color of histogram
- **dialogs**: Fixed some bugs related to PyQt6
- **video.py**: Fixed threading
- **video.py**: Removed unnecessary code that might corrupt already terminated threads

### 🧹 Refactor

- Minor refactoring
- **main_controller.py**: Update init of logger
- **main_controller**: Improved closing of the application, removed async operation
- **model**: Data-classes a bit more lightweight, less dependend
- **file_cache**: Moved to own subpackage
- **media**: Rework media-player&reader + data-model

### 🏎️ Performance

- **media_reader**: Improved flexibility

### 🔨 Build

- **annotation_tool**: Rename /src -> /annotation_tool

## 0.6.0 (2022-12-19)

### 🚀 Feature

- **histogram.py**: Switch from matplotlib to pyqtgraph
- **local_files.py**: Added dialog for displaying local files
- **manual_annotation**: Added reset/delete action
- **annotation/controller.py**: Added copy&paste and jump-(next/prev) features

### 🐛 Fix

- **histogram.py**: Fix histogram
- **annotation/manual/controller.py**: Fixed missing some timeline updates
- **main.py**: Fixed imports & high-dpi scaling

### 🧹 Refactor

- **hist_copy.py**: Removed unnecessary module
- **player.py**: Removed unecessary assertions

## 0.5.0 (2022-12-12)

### 🚀 Feature

- **user_actions-&-timeline**: Added user_actions to simplify signal handling & Added scrolling to timeline
- **timeline.py**: Updated zooming of timeline
- **network_list.py**: Added network wrapper for adding/updating/deleting models
- **timeline.py**: First primitive not yet functioning version of the scrollable timeline
- **main.py**: High-DPI scaling is now used if selected by the user
- **settings_dialog.py**: Improved the design of the settings
- **annotation-list-and-settings-dialog**: Updated some GUI Dialoges
- Implemented file based caching for persisting Annotations, Datasets, etc
- **file_cache.py**: Added file based cache to replace __local_storage__
- **video_reader.py**: Added pythonic video reading

### 🐛 Fix

- **mocap.py**: Fixed scaling
- **annotation_dialog-&-timeline**: Fixed handling of empty annotations
- **networks**: Fixed network loading
- Fixed some small bugs

### 🧹 Refactor

- Resize annotation-displaying widget

## 0.4.0 (2022-11-11)

### 🚀 Feature

- **priority_queue.py**: Added priority_queue for faster retrieval loading
- **src/annotation/retrieval/controller**: Added loading-thread and progress-dialog to the retrieval controller, network is now running in its own thread such that the GUI is not frozen in the meantime
- make __version__ string available to the package

### 🐛 Fix

- **mocap_reader.py**: Adjusted Mocap-reading to the default LARa format
- **retrieval/query.py**: Small fix to __compute_open_elements__
- **priority_queue.py**: Added queue
- **export_annotoation_dialog.py**: Fixed handling of too short input-files
- Fixed a error that happened when loading retrieval-mode after the previous GUI-updates
- **timeline.py**: Fixed scaling issue where the pointer-position (green line on timeline) got out of sync after rescaling the app's window

### 🧹 Refactor

- **network/controller.py**: Changed caching to use lru_cache and added cuda_available checking
- **rerieval-mode**: Moved mocap-reader to another package, some more docs
- **retrieval/controller.py**: Added some caching and changed back to cdist-computation of the distances
- **retrieval-mode**: Refactoring the code, some assertions added to ensure correctness of query
- **retrieval-mode**: Reworking the retrieval-(annotation)mode
- **settings.py**: Updated settings and settings-dialog
- **mocap_reader.py**: Rewriting mocap-reading to be on-demand and less memory-intensive
- **new_annotation_dialog.py**: Better error-msg for unsupported media-type
- Changed button names to better represent their behavior/actions, also added some tooltips
- Move __version__ from __version__.py to __init__.py

### 🏎️ Performance

- **retrieval/**: Improved retrieval speed & histogram-computation
- **retrieval/controller.py**: Improved retrieval-queue by using nested priority-queues
- **priority_queue.py**: Improving the queue

## 0.3.1 (2022-10-20)

### 🐛 Fix

- Pipeline config

## 0.3.0 (2022-10-20)

### Added

- Makefile for building and testing locally
- `README.md` with installation instructions
- Added a license
- Dummy Retrieval mode

### Changed

- Dependencies are now specified in `pyproject.toml` rather than in `requirements.txt`.
- Code formatting with `black`.

