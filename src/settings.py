from dataclasses import dataclass, field, fields

from src.utility.file_cache import cached


@cached
@dataclass
class Settings:
    annotator_id: int = field(init=False, default=0)
    debugging_mode: bool = field(init=False, default=False)
    window_x: int = field(init=False, default=1200)
    window_y: int = field(init=False, default=700)
    darkmode: bool = field(init=False, default=False)
    font: int = field(init=False, default=10)
    refresh_rate: int = field(init=False, default=200)
    retrieval_segment_size: int = field(init=False, default=200)
    retrieval_segment_overlap: float = field(init=False, default=0)
    small_skip: int = field(init=False, default=1)
    big_skip: int = field(init=False, default=100)

    def reset(self):
        for fld in fields(self):
            setattr(self, fld.name, fld.default)

    def as_dict(self):
        return {fld.name: getattr(self, fld.name) for fld in fields(self)}

    def from_dict(self, dct):
        for fld in fields(self):
            setattr(self, fld.name, dct.get(fld.name, fld.default))


settings = Settings.get_all()
assert len(settings) <= 1, "There should only be one settings object"
if len(settings) == 0:
    settings = Settings()
else:
    settings = settings[0]
