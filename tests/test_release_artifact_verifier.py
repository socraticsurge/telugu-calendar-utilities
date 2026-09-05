"""Unit coverage for the PyPI artifact license/dependency gate."""

from __future__ import annotations

import io
import tarfile
import warnings
import zipfile
from pathlib import Path

import pytest

from tools.verify_release_artifacts import (
    ArtifactVerificationError,
    verify_release_artifacts,
)

NAME = "mcp-server-panchangam"
NORMALIZED_NAME = "mcp_server_panchangam"
VERSION = "1.18.1"
DEPENDENCY = "pyswisseph==2.10.3.2"


def _metadata(*dependencies: str) -> bytes:
    requires_dist = "".join(
        f"Requires-Dist: {dependency}\n" for dependency in dependencies
    )
    return (
        "Metadata-Version: 2.4\n"
        f"Name: {NAME}\n"
        f"Version: {VERSION}\n"
        "License-Expression: AGPL-3.0-or-later\n"
        "License-File: LICENSE\n"
        "License-File: THIRD_PARTY_NOTICES.md\n"
        f"{requires_dist}\n"
    ).encode()


def _add_tar_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    member = tarfile.TarInfo(name)
    member.size = len(data)
    archive.addfile(member, io.BytesIO(data))


def _write_wheel_fixture(
    artifact_dir: Path,
    root: Path,
    *,
    wheel_dependencies: tuple[str, ...],
    wheel_native: str | None,
    wheel_source: bytes,
    wheel_duplicate_source: bool,
) -> None:
    dist_info = f"{NORMALIZED_NAME}-{VERSION}.dist-info"
    wheel = artifact_dir / f"{NORMALIZED_NAME}-{VERSION}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, mode="w") as archive:
        archive.writestr(f"{dist_info}/METADATA", _metadata(*wheel_dependencies))
        archive.writestr(
            f"{dist_info}/licenses/LICENSE", (root / "LICENSE").read_bytes()
        )
        archive.writestr(
            f"{dist_info}/licenses/THIRD_PARTY_NOTICES.md",
            (root / "THIRD_PARTY_NOTICES.md").read_bytes(),
        )
        source_name = "telugu_panchangam/__init__.py"
        archive.writestr(source_name, wheel_source)
        if wheel_duplicate_source:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(source_name, wheel_source)
        if wheel_native is not None:
            archive.writestr(wheel_native, b"native")


def _write_sdist_fixture(
    artifact_dir: Path,
    root: Path,
    *,
    sdist_attack: str | None,
    sdist_pyproject: str,
    sdist_source: bytes,
    sdist_duplicate_source: bool,
) -> None:
    prefix = f"{NORMALIZED_NAME}-{VERSION}"
    sdist = artifact_dir / f"{prefix}.tar.gz"
    with tarfile.open(sdist, mode="w:gz") as archive:
        _add_tar_bytes(archive, f"{prefix}/PKG-INFO", _metadata(DEPENDENCY))
        _add_tar_bytes(archive, f"{prefix}/LICENSE", (root / "LICENSE").read_bytes())
        _add_tar_bytes(
            archive,
            f"{prefix}/THIRD_PARTY_NOTICES.md",
            (root / "THIRD_PARTY_NOTICES.md").read_bytes(),
        )
        source_name = f"{prefix}/telugu_panchangam/__init__.py"
        _add_tar_bytes(archive, source_name, sdist_source)
        if sdist_duplicate_source:
            _add_tar_bytes(archive, source_name, sdist_source)
        if sdist_pyproject != "missing":
            pyproject = (root / "pyproject.toml").read_bytes()
            if sdist_pyproject == "conflicting":
                pyproject = pyproject.replace(
                    DEPENDENCY.encode(), b"pyswisseph>=2.10.3"
                )
            _add_tar_bytes(archive, f"{prefix}/pyproject.toml", pyproject)
        if sdist_attack == "native":
            _add_tar_bytes(archive, f"{prefix}/vendor/library.so", b"native")
        elif sdist_attack == "versioned-native":
            _add_tar_bytes(archive, f"{prefix}/vendor/libswisseph.so.1.2", b"native")
        elif sdist_attack == "traversal":
            _add_tar_bytes(archive, f"{prefix}/../escape.py", b"escape")
        elif sdist_attack == "windows-traversal":
            _add_tar_bytes(archive, f"{prefix}/..\\..\\escape.py", b"escape")
        elif sdist_attack == "symlink":
            member = tarfile.TarInfo(f"{prefix}/linked-source.py")
            member.type = tarfile.SYMTYPE
            member.linkname = "../../outside.py"
            archive.addfile(member)


def _fixture_release(
    tmp_path: Path,
    *,
    wheel_dependencies: tuple[str, ...] = (DEPENDENCY,),
    wheel_native: str | None = None,
    wheel_source: bytes = b"",
    wheel_duplicate_source: bool = False,
    sdist_attack: str | None = None,
    sdist_pyproject: str = "aligned",
    sdist_source: bytes = b"",
    sdist_duplicate_source: bool = False,
) -> tuple[Path, Path]:
    root = tmp_path / "root"
    artifact_dir = tmp_path / "dist"
    package = root / "telugu_panchangam"
    package.mkdir(parents=True)
    artifact_dir.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (root / "LICENSE").write_text("AGPL fixture\n", encoding="utf-8")
    (root / "THIRD_PARTY_NOTICES.md").write_text(
        "## PySwissEph 2.10.3.2\n", encoding="utf-8"
    )
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "{NAME}"\nversion = "{VERSION}"\n'
        f'dependencies = [\n    "{DEPENDENCY}",\n]\n',
        encoding="utf-8",
    )

    _write_wheel_fixture(
        artifact_dir,
        root,
        wheel_dependencies=wheel_dependencies,
        wheel_native=wheel_native,
        wheel_source=wheel_source,
        wheel_duplicate_source=wheel_duplicate_source,
    )
    _write_sdist_fixture(
        artifact_dir,
        root,
        sdist_attack=sdist_attack,
        sdist_pyproject=sdist_pyproject,
        sdist_source=sdist_source,
        sdist_duplicate_source=sdist_duplicate_source,
    )
    return artifact_dir, root


def test_release_artifact_verifier_accepts_aligned_archives(tmp_path: Path) -> None:
    artifact_dir, root = _fixture_release(tmp_path)

    verify_release_artifacts(artifact_dir, root=root)


def test_release_artifact_verifier_rejects_broad_wheel_dependency(
    tmp_path: Path,
) -> None:
    artifact_dir, root = _fixture_release(
        tmp_path, wheel_dependencies=("pyswisseph>=2.10.3",)
    )

    with pytest.raises(ArtifactVerificationError, match="only the exact pyswisseph"):
        verify_release_artifacts(artifact_dir, root=root)


def test_release_artifact_verifier_rejects_duplicate_pyswisseph_requirements(
    tmp_path: Path,
) -> None:
    artifact_dir, root = _fixture_release(
        tmp_path,
        wheel_dependencies=(DEPENDENCY, "PySwissEph>=2.10.3"),
    )

    with pytest.raises(ArtifactVerificationError, match="only the exact pyswisseph"):
        verify_release_artifacts(artifact_dir, root=root)


@pytest.mark.parametrize(
    "artifact",
    ["wheel", "sdist"],
)
def test_release_artifact_verifier_rejects_stale_package_source(
    tmp_path: Path, artifact: str
) -> None:
    kwargs = {f"{artifact}_source": b"stale source"}
    artifact_dir, root = _fixture_release(tmp_path, **kwargs)

    with pytest.raises(ArtifactVerificationError, match="stale package source"):
        verify_release_artifacts(artifact_dir, root=root)


@pytest.mark.parametrize(
    "artifact",
    ["wheel", "sdist"],
)
def test_release_artifact_verifier_rejects_duplicate_package_source(
    tmp_path: Path, artifact: str
) -> None:
    kwargs = {f"{artifact}_duplicate_source": True}
    artifact_dir, root = _fixture_release(tmp_path, **kwargs)

    with pytest.raises(ArtifactVerificationError, match="must contain exactly one"):
        verify_release_artifacts(artifact_dir, root=root)


def test_release_artifact_verifier_rejects_extra_publishable_content(
    tmp_path: Path,
) -> None:
    artifact_dir, root = _fixture_release(tmp_path)
    (artifact_dir / "unverified.whl").write_bytes(b"unverified")

    with pytest.raises(ArtifactVerificationError, match="only the verified"):
        verify_release_artifacts(artifact_dir, root=root)


@pytest.mark.parametrize(
    ("sdist_pyproject", "message"),
    [
        ("missing", "must contain exactly one.*pyproject.toml"),
        ("conflicting", "stale pyproject.toml"),
    ],
)
def test_release_artifact_verifier_rejects_bad_sdist_build_metadata(
    tmp_path: Path, sdist_pyproject: str, message: str
) -> None:
    artifact_dir, root = _fixture_release(tmp_path, sdist_pyproject=sdist_pyproject)

    with pytest.raises(ArtifactVerificationError, match=message):
        verify_release_artifacts(artifact_dir, root=root)


def test_release_artifact_verifier_rejects_versioned_native_wheel(
    tmp_path: Path,
) -> None:
    artifact_dir, root = _fixture_release(
        tmp_path, wheel_native="telugu_panchangam/vendor/libswisseph.so.1"
    )

    with pytest.raises(ArtifactVerificationError, match="bundles native libraries"):
        verify_release_artifacts(artifact_dir, root=root)


@pytest.mark.parametrize(
    ("attack", "message"),
    [
        ("native", "bundles native libraries"),
        ("versioned-native", "bundles native libraries"),
        ("traversal", "unsafe path"),
        ("windows-traversal", "unsafe path"),
        ("symlink", "link or special member"),
    ],
)
def test_release_artifact_verifier_rejects_unsafe_sdist_members(
    tmp_path: Path, attack: str, message: str
) -> None:
    artifact_dir, root = _fixture_release(tmp_path, sdist_attack=attack)

    with pytest.raises(ArtifactVerificationError, match=message):
        verify_release_artifacts(artifact_dir, root=root)
