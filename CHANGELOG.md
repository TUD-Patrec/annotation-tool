# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). See also [RELEASE.md](RELEASE.md) for additional explanation.

## Unreleased

### Feature

- **src/annotation/retrieval/controller**: Added loading-thread and progress-dialog to the retrieval controller, network is now running in its own thread such that the GUI is not frozen in the meantime
- make __version__ string available to the package

### Fix

- **export_annotoation_dialog.py**: Fixed handling of too short input-files
- Fixed a error that happened when loading retrieval-mode after the previous GUI-updates
- **timeline.py**: Fixed scaling issue where the pointer-position (green line on timeline) got out of sync after rescaling the app's window

### Refactor

- **settings.py**: Updated settings and settings-dialog
- **mocap_reader.py**: Rewriting mocap-reading to be on-demand and less memory-intensive
- **new_annotation_dialog.py**: Better error-msg for unsupported media-type
- Changed button names to better represent their behavior/actions, also added some tooltips
- Move __version__ from __version__.py to __init__.py

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

