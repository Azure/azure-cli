import json
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, cast

from tox import helper

from ..api import Pep517VirtualEnvPackage


class Pep517VirtualEnvPackageArtifact(Pep517VirtualEnvPackage, ABC):
    @property
    @abstractmethod
    def build_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def extra(self) -> Dict[str, Any]:
        raise NotImplementedError

    def _build_artifact(self) -> List[Path]:
        with TemporaryDirectory() as path:
            out_file = Path(path) / "out.json"
            dest = cast(Path, self.conf["pkg_dir"])
            if dest.exists():
                shutil.rmtree(str(dest))
            dest.mkdir()
            cmd = [
                "python",
                helper.isolated_builder(),
                out_file,
                dest,
                self.build_type,
                json.dumps(self.extra),
                self.build_backend_module,
            ]
            if self.build_backend_obj:
                cmd.append(self.build_backend_obj)
            result = self.execute(cmd=cmd, allow_stdin=False, cwd=self.core["tox_root"])
            result.assert_success(self.logger)
            with open(str(out_file)) as file_handler:
                base_name = json.load(file_handler)  # type:str
        return [dest / base_name]

    def perform_packaging(self) -> List[Path]:
        """build_wheel/build_sdist"""
        if self._package is None:
            self.ensure_setup()
            self._package = self._build_artifact()
        return self._package
