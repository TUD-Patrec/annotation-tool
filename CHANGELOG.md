# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). See also [RELEASE.md](RELEASE.md) for additional explanation.

## v0.4.0 (2022-11-11)

### Feature

- **priority_queue.py**: Added priority_queue for faster retrieval loading
- **src/annotation/retrieval/controller**: Added loading-thread and progress-dialog to the retrieval controller, network is now running in its own thread such that the GUI is not frozen in the meantime
- make __version__ string available to the package

### Fix

- **mocap_reader.py**: Adjusted Mocap-reading to the default LARa format
- **retrieval/query.py**: Small fix to __compute_open_elements__
- **priority_queue.py**: Added queue
- **export_annotoation_dialog.py**: Fixed handling of too short input-files
- Fixed a error that happened when loading retrieval-mode after the previous GUI-updates
- **timeline.py**: Fixed scaling issue where the pointer-position (green line on timeline) got out of sync after rescaling the app's window

### Refactor

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

### Performance

- **retrieval/**: Improved retrieval speed & histogram-computation
- **retrieval/controller.py**: Improved retrieval-queue by using nested priority-queues
- **priority_queue.py**: Improving the queue

## 0.3.1 (2022-10-20)

### Fixed

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

