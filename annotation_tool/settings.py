from dataclasses import dataclass, field, fields
import logging

from annotation_tool.file_cache import cached


@cached
@dataclass
class Settings:
    annotator_id: int = field(init=False, default=0)
    big_skip: int = field(init=False, default=100)
    color_theme: str = field(init=False, default="light")
    font_size: int = field(init=False, default=10)
    logging_level: int = field(init=False, default=logging.WARNING)
    merging_mode: str = field(init=False, default="into")
    preferred_width: int = field(init=False, default=1200)
    preferred_height: int = field(init=False, default=700)
    timeline_design: str = field(init=False, default="rounded")
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


_cached_settings = Settings.get_all()
if len(_cached_settings) == 0:
    settings = Settings()
else:
    settings = _cached_settings[0]
