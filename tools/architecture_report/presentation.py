"""Stable human-readable architecture report formatting."""
from __future__ import annotations


def _summary(report: dict) -> str:
    modules = sorted(
        report['modules'],
        key=lambda item: (-item['nonblank_lines'], item['path']),
    )
    manual = sum(
        item['strategy'] == 'manual-mirror'
        for item in report['duplicate_contracts']
    )
    lines = [
        f"Source commit: {report['source_commit']}",
        f"Production modules: {report['scope']['source_files']}",
        (
            'Established production modules: '
            f"{report['scope']['established_source_files']}"
        ),
        (
            'Additive feature modules: '
            f"{report['scope']['additive_feature_source_files']}"
        ),
        f"Computation records: {report['scope']['computation_records']}",
        f'Manual duplicate-contract groups: {manual}',
        'Largest modules by nonblank lines:',
    ]
    lines.extend(
        f"  {item['nonblank_lines']:4d}  {item['path']}"
        for item in modules[:10]
    )
    lines.append('Most frequently changed files in the measured history:')
    lines.extend(
        f"  {item['commits']:3d} commits / {item['churn']:5d} churn  {item['path']}"
        for item in report['history_top_changed_files'][:10]
    )
    lines.append('Highest direct test blast radius:')
    lines.extend(
        f"  {item['linked_test_count']:3d} tests / "
        f"{item['linked_computation_count']:2d} computations  {item['path']}"
        for item in report['test_blast_radius'][:10]
    )
    return '\n'.join(lines)
