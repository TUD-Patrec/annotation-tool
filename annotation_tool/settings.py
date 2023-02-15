from dataclasses import dataclass, field, fields
import json
import logging
import os

from annotation_tool import file_cache


@dataclass
class Settings:
    annotator_id: int = field(init=False, default=0)
    big_skip: int = field(init=False, default=100)
    darkmode: bool = field(init=False, default=False)
    font_size: int = field(init=False, default=10)
    logging_level: int = field(init=False, default=logging.WARNING)
    preferred_width: int = field(init=False, default=1200)
    preferred_height: int = field(init=False, default=700)
    refresh_rate: int = field(init=False, default=200)
    retrieval_segment_overlap: float = field(init=False, default=0)
    retrieval_segment_size: int = field(init=False, default=200)
    small_skip: int = field(init=False, default=1)

    def reset(self):
        for fld in fields(self):
            setattr(self, fld.name, fld.default)

    def get_default(self, name):
        for fld in fields(self):
            if fld.name == name:
                return fld.default

    def as_dict(self):
        return {fld.name: getattr(self, fld.name) for fld in fields(self)}

    def from_dict(self, dct):
        for fld in fields(self):
            setattr(self, fld.name, dct.get(fld.name, fld.default))

    def _write_to_file(self, path):
        with open(path, "w") as f:
            json.dump(self.as_dict(), f, indent=4)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        self._write_to_file(__settings_path__)


__settings_path__ = os.path.join(file_cache.application_path(), "settings.json")
print(f"Settings path: {__settings_path__}")
config = (
    json.load(open(__settings_path__, "r")) if os.path.exists(__settings_path__) else {}
)
settings = Settings()
if config:
    settings.from_dict(config)
