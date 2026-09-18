"""Keep canonical documentation changes on the normal publication path."""

import fnmatch
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-landing.yml"


def _workflow():
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def _triggers_deployment(path):
    patterns = _workflow()["on"]["push"]["paths"]
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


@pytest.mark.parametrize("path", [
    "docs/index.md",
    "docs/reference/03-computational-features.md",
    "docs/reference/computations.json",
    "docs/reference/provenance.json",
    "docs/public/docs-mark-light.svg",
    "docs/screenshots/review.png",
    ".vitepress/config.ts",
    ".vitepress/theme/index.ts",
    ".github/workflows/deploy-landing.yml",
    "tools/markdown-mermaid-fences.mjs",
])
def test_documentation_inputs_trigger_publication(path):
    assert _triggers_deployment(path), f"Documentation input is not published: {path}"


def test_all_documentation_build_tools_trigger_publication():
    scripts = json.loads((ROOT / "package.json").read_text())["scripts"]
    commands = scripts["build:docs"] + " " + scripts["docs:check-output"]
    tools = re.findall(r"node (tools/[\w-]+\.mjs)", commands)
    assert tools, "Documentation build must declare its tool inputs"
    assert all(_triggers_deployment(path) for path in tools)


def test_documentation_publication_preserves_deployment_boundaries():
    workflow = _workflow()
    assert workflow["on"]["push"]["branches"] == ["master"]
    assert "workflow_dispatch" in workflow["on"]
    assert workflow["concurrency"] == {
        "group": "gh-pages-deploy",
        "cancel-in-progress": "false",
    }
    steps = workflow["jobs"]["deploy"]["steps"]
    publisher = next(step for step in steps if "publish_dir" in step.get("with", {}))
    assert publisher["with"]["cname"] == "panchangam.astrochaganti.com"
    assert publisher["with"]["publish_dir"] == "./dist"
    assert publisher["with"]["keep_files"] == "true"


def test_unrelated_python_change_does_not_trigger_landing_deployment():
    assert not _triggers_deployment("telugu_panchangam/engines/drik.py")
