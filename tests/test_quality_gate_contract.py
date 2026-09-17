"""Keep analysis credentials isolated and coverage imports explicit."""

import configparser
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_sonar_job_consumes_successful_same_run_coverage_without_running_tests():
    workflow = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
    job = workflow['jobs']['sonar-analysis']
    assert "'branch Sonar analysis' || 'Sonar analysis'" in job['name']
    assert set(job['needs']) == {'scope', 'test', 'frontend-and-browser'}
    assert job['permissions'] == {'contents': 'read'}
    assert 'pull_request_target' not in workflow.get('on', workflow.get(True, {}))
    assert job.get('continue-on-error', False) is False
    checkout = job['steps'][0]['with']
    assert checkout == {'fetch-depth': 0, 'persist-credentials': False}
    downloads = [step['with'] for step in job['steps'] if 'download-artifact@' in step.get('uses', '')]
    assert downloads == [
        {'name': 'python-coverage', 'path': 'coverage/python'},
        {'name': 'frontend-coverage', 'path': 'coverage/frontend'},
    ]
    scanner = [step for step in job['steps'] if 'sonarqube-scan-action@' in step.get('uses', '')]
    assert len(scanner) == 1
    assert scanner[0]['env'] == {'SONAR_TOKEN': '${{ secrets.SONAR_TOKEN }}'}
    assert '-Dsonar.qualitygate.wait=true' in scanner[0]['with']['args']
    scripts = [step for step in job['steps'] if 'run' in step]
    assert len(scripts) == 1
    assert scripts[0]['name'] == 'Require zero new Sonar issues on this pull request'
    assert 'SONAR_TOKEN' not in str(scripts[0])
    assert 'curl --fail' in scripts[0]['run']
    assert 'jq --exit-status' in scripts[0]['run']
    assert '.periods[0].value == "0"' in scripts[0]['run']
    for name in ('test', 'frontend-and-browser'):
        assert 'SONAR_TOKEN' not in str(workflow['jobs'][name])


def test_coverage_uploads_fail_if_missing_and_are_not_cross_run():
    workflow = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
    for name, artifact in [('test', 'python-coverage'), ('frontend-and-browser', 'frontend-coverage')]:
        uploads = [step for step in workflow['jobs'][name]['steps'] if 'upload-artifact@' in step.get('uses', '')]
        assert len(uploads) == 1
        assert uploads[0]['with']['name'] == artifact
        assert uploads[0]['with']['if-no-files-found'] == 'error'
    assert "'lcov'" in (ROOT / 'vite.config.ts').read_text()


def test_sonar_scope_preserves_sources_and_classifies_tests():
    properties = dict(
        line.split('=', 1) for line in (ROOT / 'sonar-project.properties').read_text().splitlines()
        if line and not line.startswith('#')
    )
    assert properties['sonar.sources'] == '.'
    assert properties['sonar.tests'] == '.'
    assert properties['sonar.test.inclusions'] == 'tests/**,src/**/__tests__/**'
    assert properties['sonar.python.version'] == '3.10,3.11,3.12,3.13'
    assert properties['sonar.sourceEncoding'] == 'UTF-8'
    assert properties['sonar.python.coverage.reportPaths'] == 'coverage/python/coverage.xml'
    assert properties['sonar.javascript.lcov.reportPaths'] == 'coverage/frontend/lcov.info'
    assert 'sonar.coverage.exclusions' not in properties
    assert 'sonar.issue.ignore.multicriteria' not in properties


def test_python_coverage_tracks_unexecuted_application_and_tooling_files():
    config = configparser.ConfigParser()
    config.read(ROOT / '.coveragerc')
    assert config.getboolean('run', 'branch')
    assert config.getboolean('run', 'relative_files')
    assert config['run']['source'] == '.'
    assert set(config['report']['include'].split()) == {'telugu_panchangam/*', 'tools/*'}
    assert config['xml']['output'] == 'coverage/python/coverage.xml'


@pytest.mark.parametrize('case', [
    ([{'metric': 'new_violations', 'periods': [{'value': '0'}]}], '605', '0', True),
    ([{'metric': 'new_violations', 'periods': [{'value': '1'}]}], '605', '0', False),
    ([{'metric': 'new_violations', 'periods': [{'value': '0'}]}], '604', '0', False),
    ([{'metric': 'new_violations', 'periods': [{'value': '0'}]}], '605', '22', False),
    ([], '605', '0', False),
    ([{'metric': 'new_violations'}], '605', '0', False),
])
@pytest.mark.parametrize('reported_sha', ['current-head', 'stale-head', None])
@pytest.mark.parametrize('code_smells', [0, 1])
def test_zero_issue_step_fails_closed(tmp_path, case, reported_sha, code_smells):
    measures, pr, http_status, passes = case
    workflow = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
    step = workflow['jobs']['sonar-analysis']['steps'][-1]
    assert step['shell'] == 'bash'
    curl = tmp_path / 'curl'
    curl.write_text(
        '#!/bin/sh\ncase "$*" in\n'
        '*project_pull_requests*) printf "%s" "$SONAR_TEST_PR_JSON" ;;\n'
        '*) printf "%s" "$SONAR_TEST_JSON" ;;\nesac\nexit "$SONAR_TEST_HTTP_STATUS"\n'
    )
    curl.chmod(0o700)
    env = {
        **os.environ, 'PATH': f"{tmp_path}:{os.environ['PATH']}", 'SONAR_PR': '605',
        'SONAR_SHA': 'current-head',
        'SONAR_TEST_JSON': json.dumps({'component': {'pullRequest': pr, 'measures': measures}}),
        'SONAR_TEST_PR_JSON': json.dumps({'pullRequests': [{
            'key': pr, 'commit': {'sha': reported_sha},
            'status': {'qualityGateStatus': 'OK', 'bugs': 0, 'vulnerabilities': 0, 'codeSmells': code_smells},
        }]}),
        'SONAR_TEST_HTTP_STATUS': http_status,
    }
    result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', step['run']], env=env, capture_output=True)
    assert (result.returncode == 0) is (passes and reported_sha == 'current-head' and code_smells == 0)
