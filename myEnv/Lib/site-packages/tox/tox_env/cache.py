import json
from contextlib import contextmanager
from pathlib import Path


class Cache:
    def __init__(self, path: Path) -> None:
        self._path = path
        try:
            value = json.loads(self._path.read_text())
        except (ValueError, OSError):
            value = {}
        self._content = value

    @contextmanager
    def compare(self, value, section, sub_section=None):
        old = self._content.get(section)
        if sub_section is not None and old is not None:
            old = old.get(sub_section)

        if old == value:
            yield True, None
        else:
            yield False, old
            # if no exception thrown update
            if sub_section is None:
                self._content[section] = value
            else:
                if self._content.get(section) is None:
                    self._content[section] = {sub_section: value}
                else:
                    self._content[section][sub_section] = value
            self._write()

    def update(self, section, value):
        self._content[section] = value

    def _write(self):
        self._path.write_text(json.dumps(self._content, indent=2))
