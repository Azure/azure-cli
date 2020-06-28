import json
from abc import ABC
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple, cast

import toml
from packaging.requirements import Requirement

from tox import helper
from tox.config.sets import ConfigSet
from tox.tox_env.python.package import PythonPackage

from ..api import VirtualEnv

try:
    import importlib.metadata as imp_meta
except ImportError:
    import importlib_metadata as imp_meta


TOX_PACKAGE_ENV_ID = "virtualenv-pep-517"


class PackageType(Enum):
    sdist = 1
    wheel = 2
    dev = 3
    skip = 4


class Pep517VirtualEnvPackage(VirtualEnv, PythonPackage, ABC):
    """local file system python virtual environment via the virtualenv package"""

    LEGACY_BUILD_BACKEND = "setuptools.build_meta:__legacy__"
    LEGACY_REQUIRES = ["setuptools >= 40.8.0", "wheel"]

    def __init__(self, conf: ConfigSet, core: ConfigSet, options) -> None:
        super().__init__(conf, core, options)
        backend_module, backend_object, requires = self.load_builder_and_requires()
        self._requires = requires  # type: List[Requirement]
        self.build_backend_module = backend_module  # type:str
        self.build_backend_obj = backend_object  # type: Optional[str]
        self._distribution_meta = None  # type:Optional[imp_meta.PathDistribution]
        self._build_requires = None  # type:Optional[List[Requirement]]
        self._package = None  # type:Optional[Requirement]

    def load_builder_and_requires(self) -> Tuple[str, Optional[str], List[Requirement]]:
        py_project_toml = cast(Path, self.core["tox_root"]) / "pyproject.toml"
        if py_project_toml.exists():
            py_project = toml.load(py_project_toml)
            build_backend = py_project.get("build-system", {}).get("build-backend", self.LEGACY_BUILD_BACKEND)
            requires = py_project.get("build-system", {}).get("requires", self.LEGACY_REQUIRES)
        else:
            build_backend = self.LEGACY_BUILD_BACKEND
            requires = self.LEGACY_REQUIRES
        req_as_req = [Requirement(i) for i in requires]
        build_backend_info = build_backend.split(":")
        backend_module = build_backend_info[0]
        backend_obj = build_backend_info[1] if len(build_backend_info) > 1 else None
        return backend_module, backend_obj, req_as_req

    def register_config(self):
        super().register_config()
        self.conf.add_config(
            keys=["meta_dir"],
            of_type=Path,
            default=lambda conf, name: conf[name]["env_dir"] / ".meta",
            desc="directory assigned to the tox environment",
        )
        self.conf.add_config(
            keys=["pkg_dir"],
            of_type=Path,
            default=lambda conf, name: conf[name]["env_dir"] / "dist",
            desc="directory assigned to the tox environment",
        )

    def requires(self) -> List[Requirement]:
        return self._requires

    def build_requires(self) -> List[Requirement]:
        """get_requires_for_build_sdist/get-requires-for-build-wheel"""
        if self._build_requires is None:

            with TemporaryDirectory() as path:
                requires_file = Path(path) / "out.json"
                cmd = ["python", helper.build_requires(), requires_file, self.build_backend_module]
                if self.build_backend_obj:
                    cmd.append(self.build_backend_obj)
                result = self.execute(cmd=cmd, allow_stdin=False)
                result.assert_success(self.logger)
                with open(str(requires_file)) as file_handler:
                    self._build_requires = json.load(file_handler)
        return self._build_requires

    def get_package_dependencies(self, extras=None) -> List[Requirement]:
        self._ensure_meta_present()
        if extras is None:
            extras = set()
        result = []
        requires = self._distribution_meta.requires or []
        for v in requires:
            req = Requirement(v)
            markers = getattr(req.marker, "_markers", ()) or ()
            for _at, (m_key, op, m_val) in (
                (j, i) for j, i in enumerate(markers) if isinstance(i, tuple) and len(i) == 3
            ):
                if m_key.value == "extra" and op.value == "==":
                    extra = m_val.value
                    break
            else:
                extra, _at = None, None
            if extra is None or extra in extras:
                if _at is not None:
                    # noinspection PyProtectedMember
                    del markers[_at]
                    _at -= 1
                    if _at > 0 and markers[_at] in ("and", "or"):
                        del markers[_at]
                    # noinspection PyProtectedMember
                    if len(markers) == 0:
                        req.marker = None
                result.append(req)
        return result

    def _ensure_meta_present(self):
        if self._distribution_meta is None:
            self.ensure_setup()
            self.meta_folder.mkdir(exist_ok=True)
            cmd = [
                "python",
                helper.wheel_meta(),
                self.meta_folder,
                json.dumps(self.meta_flags),
                self.build_backend_module,
            ]
            if self.build_backend_obj:
                cmd.append(self.build_backend_obj)
            result = self.execute(cmd=cmd, allow_stdin=False)
            result.assert_success(self.logger)
            dist_info = next(self.meta_folder.iterdir())
            self._distribution_meta = imp_meta.Distribution.at(dist_info)

    @property
    def meta_folder(self) -> Path:
        return cast(Path, self.conf["meta_dir"])

    @property
    def meta_flags(self):
        return {"config_settings": None}
