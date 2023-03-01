from dataclasses import dataclass, field, fields
import logging

from annotation_tool.file_cache import cached


@cached
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


settings = Settings.get_all()
if len(settings) == 0:
    settings = Settings()
else:
    if len(settings) > 1:
        logging.warning("Found multiple cached settings-objects. Using the first one.")
    settings = settings[0]
