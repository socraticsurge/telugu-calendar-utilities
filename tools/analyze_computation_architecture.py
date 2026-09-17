#!/usr/bin/env python3
"""Produce reproducible computation-layer coupling and change-risk evidence.

The report is descriptive, not an architecture score or a refactoring mandate.
This module retains the documented CLI and existing imported entrypoints.
"""
from __future__ import annotations

import argparse
import json

if __package__:
    from .architecture_report.presentation import _summary
    from .architecture_report.report import DEFAULT_HISTORY_COMMITS, build_report
    from .architecture_report.scope import _layer, source_scope_class
else:
    from architecture_report.presentation import _summary
    from architecture_report.report import DEFAULT_HISTORY_COMMITS, build_report
    from architecture_report.scope import _layer, source_scope_class

__all__ = ['_layer', '_summary', 'build_report', 'source_scope_class']


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--commits', type=int, default=DEFAULT_HISTORY_COMMITS)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report(args.ref, args.commits)
    if args.summary:
        print(_summary(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
