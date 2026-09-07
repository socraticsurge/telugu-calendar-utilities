"""Verify the license and dependency boundary of built PyPI artifacts."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
LICENSE_EXPRESSION = "AGPL-3.0-or-later"
LICENSE_FILES = ("LICENSE", "THIRD_PARTY_NOTICES.md")
NATIVE_SUFFIXES = (".dll", ".dylib", ".pyd")


class ArtifactVerificationError(RuntimeError):
    """Raised when a release artifact violates the publication contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactVerificationError(message)


def _project_contract(root: Path) -> tuple[str, str, str]:
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    name_match = re.search(r'^name = "([^"]+)"$', pyproject, re.MULTILINE)
    version_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    dependency_matches = re.findall(
        r'^\s*"(pyswisseph[^"]*)",?$', pyproject, re.MULTILINE | re.IGNORECASE
    )
    _require(name_match is not None, "pyproject.toml has no project name")
    _require(version_match is not None, "pyproject.toml has no project version")
    _require(
        len(dependency_matches) == 1,
        "pyproject.toml must declare exactly one PySwissEph dependency",
    )
    dependency = dependency_matches[0]
    pin_match = re.fullmatch(r"pyswisseph==(\d+(?:\.\d+)+)", dependency)
    _require(pin_match is not None, "PySwissEph must be pinned to an exact version")
    assert name_match is not None
    assert version_match is not None
    assert pin_match is not None
    notices = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    _require(
        f"## PySwissEph {pin_match.group(1)}" in notices,
        "THIRD_PARTY_NOTICES.md does not match the pinned PySwissEph version",
    )
    return name_match.group(1), version_match.group(1), dependency


def _metadata(data: bytes, *, source: str):
    message = BytesParser(policy=policy.compat32).parsebytes(data)
    _require(message.get("Name") is not None, f"{source} metadata has no Name")
    return message


def _verify_metadata(
    message, *, source: str, name: str, version: str, dependency: str
) -> None:
    _require(message.get("Name") == name, f"{source} has the wrong project name")
    _require(message.get("Version") == version, f"{source} has the wrong version")
    _require(
        message.get("License-Expression") == LICENSE_EXPRESSION,
        f"{source} has the wrong license expression",
    )
    license_files = set(message.get_all("License-File", []))
    _require(
        set(LICENSE_FILES).issubset(license_files),
        f"{source} does not declare both license files",
    )
    dependencies = message.get_all("Requires-Dist", [])
    pyswisseph_dependencies = [
        item
        for item in dependencies
        if re.match(r"^\s*pyswisseph\b", item, re.IGNORECASE)
    ]
    _require(
        pyswisseph_dependencies == [dependency],
        f"{source} must contain only the exact {dependency} dependency",
    )


def _single_suffix(names: list[str], suffix: str, *, source: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    _require(len(matches) == 1, f"{source} must contain exactly one {suffix}")
    return matches[0]


def _single_name(names: list[str], name: str, *, source: str) -> str:
    _require(names.count(name) == 1, f"{source} must contain exactly one {name}")
    return name


def _source_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in (root / "telugu_panchangam").rglob("*.py")
    }


def _is_native_member(member: str) -> bool:
    lowered = member.lower()
    return lowered.endswith(NATIVE_SUFFIXES) or bool(
        re.search(r"\.so(?:\.[0-9a-z_-]+)*$", lowered)
    )


def _verify_wheel(
    wheel: Path, *, root: Path, name: str, version: str, dependency: str
) -> None:
    expected_files = {
        filename: (root / filename).read_bytes() for filename in LICENSE_FILES
    }
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = _single_suffix(names, ".dist-info/METADATA", source=wheel.name)
        _verify_metadata(
            _metadata(archive.read(metadata_name), source=wheel.name),
            source=wheel.name,
            name=name,
            version=version,
            dependency=dependency,
        )
        for filename, expected in expected_files.items():
            member = _single_suffix(
                names, f".dist-info/licenses/{filename}", source=wheel.name
            )
            _require(
                archive.read(member) == expected,
                f"{wheel.name} contains a stale {filename}",
            )
        for filename, expected in _source_files(root).items():
            _single_name(names, filename, source=wheel.name)
            _require(
                archive.read(filename) == expected,
                f"{wheel.name} contains stale package source: {filename}",
            )
        native_members = [member for member in names if _is_native_member(member)]
        _require(
            not native_members,
            f"{wheel.name} unexpectedly bundles native libraries: {native_members}",
        )


def _read_tar_member(archive: tarfile.TarFile, member: str, *, source: str) -> bytes:
    extracted = archive.extractfile(member)
    _require(extracted is not None, f"{source} cannot read {member}")
    assert extracted is not None
    return extracted.read()


def _verify_sdist(
    sdist: Path,
    *,
    root: Path,
    normalized_name: str,
    name: str,
    version: str,
    dependency: str,
) -> None:
    prefix = f"{normalized_name}-{version}"
    expected_files = {
        filename: (root / filename).read_bytes() for filename in LICENSE_FILES
    }
    with tarfile.open(sdist, mode="r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        for member in members:
            member_path = PurePosixPath(member.name)
            _require(
                not member_path.is_absolute()
                and ".." not in member_path.parts
                and "\\" not in member.name
                and member_path.parts
                and member_path.parts[0] == prefix,
                f"{sdist.name} contains an unsafe path: {member.name}",
            )
            _require(
                member.isfile() or member.isdir(),
                f"{sdist.name} contains a link or special member: {member.name}",
            )
        native_members = [member for member in names if _is_native_member(member)]
        _require(
            not native_members,
            f"{sdist.name} unexpectedly bundles native libraries: {native_members}",
        )
        metadata_name = f"{prefix}/PKG-INFO"
        _single_name(names, metadata_name, source=sdist.name)
        _verify_metadata(
            _metadata(
                _read_tar_member(archive, metadata_name, source=sdist.name),
                source=sdist.name,
            ),
            source=sdist.name,
            name=name,
            version=version,
            dependency=dependency,
        )
        pyproject_name = f"{prefix}/pyproject.toml"
        _single_name(names, pyproject_name, source=sdist.name)
        _require(
            _read_tar_member(archive, pyproject_name, source=sdist.name)
            == (root / "pyproject.toml").read_bytes(),
            f"{sdist.name} contains a stale pyproject.toml",
        )
        for filename, expected in expected_files.items():
            member = f"{prefix}/{filename}"
            _single_name(names, member, source=sdist.name)
            _require(
                _read_tar_member(archive, member, source=sdist.name) == expected,
                f"{sdist.name} contains a stale {filename}",
            )
        for filename, expected in _source_files(root).items():
            member = f"{prefix}/{filename}"
            _single_name(names, member, source=sdist.name)
            _require(
                _read_tar_member(archive, member, source=sdist.name) == expected,
                f"{sdist.name} contains stale package source: {filename}",
            )


def verify_release_artifacts(artifact_dir: Path, *, root: Path = ROOT) -> None:
    name, version, dependency = _project_contract(root)
    normalized_name = re.sub(r"[-_.]+", "_", name).lower()
    _require(
        artifact_dir.is_dir(), f"artifact directory does not exist: {artifact_dir}"
    )
    wheels = sorted(artifact_dir.glob(f"{normalized_name}-{version}-*.whl"))
    sdists = sorted(artifact_dir.glob(f"{normalized_name}-{version}.tar.gz"))
    _require(
        len(wheels) == 1, f"expected one wheel for {name} {version}, found {wheels}"
    )
    _require(
        len(sdists) == 1, f"expected one sdist for {name} {version}, found {sdists}"
    )
    entries = set(artifact_dir.iterdir())
    _require(
        entries == {wheels[0], sdists[0]},
        f"artifact directory must contain only the verified wheel and sdist: {sorted(entries)}",
    )
    _verify_wheel(
        wheels[0], root=root, name=name, version=version, dependency=dependency
    )
    _verify_sdist(
        sdists[0],
        root=root,
        normalized_name=normalized_name,
        name=name,
        version=version,
        dependency=dependency,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args()
    try:
        verify_release_artifacts(args.artifact_dir)
    except ArtifactVerificationError as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print("Release artifacts match the pinned dependency and AGPL source contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
