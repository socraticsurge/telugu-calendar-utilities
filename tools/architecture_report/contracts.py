"""Existing engine shape and duplicate-contract evidence; no engine execution."""
from __future__ import annotations

import ast
import re
from typing import Any

from .repository import SourceSnapshot

_ACTIVITY_RULES_ARTIFACT = 'src/data/activity-rules.generated.json'


_PANCHANGAM_NAMES = 'telugu_panchangam/panchangam_names.py'


_MUHURTA_ASTRONOMY = 'src/panels/muhurta-astronomy.ts'


_MUHURTA_DAY_PIPELINE = 'src/panels/muhurta-day-pipeline.ts'


_MUHURTA_SCORING = 'src/panels/muhurta-scoring.ts'


_DUPLICATE_CONTRACTS = {
    'activity_profiles': {
        'strategy': 'generated-from-python',
        'locations': [
            ('telugu_panchangam/personal/activity_rules.py', 'ACTIVITY_RULES'),
            (_ACTIVITY_RULES_ARTIFACT, '"rules"'),
            (_MUHURTA_DAY_PIPELINE, 'MU_ACTIVITY'),
        ],
    },
    'rashi_vocabulary': {
        'strategy': 'manual-mirror',
        'locations': [
            (_PANCHANGAM_NAMES, 'RASHI_NAMES'),
            ('src/data/rasis.ts', 'RASI_NAMES'),
            ('src/muhurta-scorer.ts', 'MU_RASHI_NAMES'),
            ('src/panels/today.ts', 'RASHI_NAMES_JS'),
        ],
    },
    'nakshatra_vocabulary': {
        'strategy': 'manual-mirror',
        'locations': [
            (_PANCHANGAM_NAMES, 'NAKSHATRA_NAMES'),
            ('src/data/rasis.ts', 'NAKSHATRA_NAMES'),
        ],
    },
    'nitya_yoga_vocabulary_and_disposition': {
        'strategy': 'manual-mirror',
        'locations': [
            (_PANCHANGAM_NAMES, 'YOGA_NAMES'),
            ('telugu_panchangam/personal/nitya_yoga.py', 'NITYA_AUSPICIOUS'),
            (_MUHURTA_ASTRONOMY, 'MU_YOGA_NAMES_27'),
            (_MUHURTA_SCORING, 'MU_NITYA_AUSPICIOUS'),
        ],
    },
    'special_yoga_tables': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/special_yogas.py', '_SARVARTHA_SIDDHI'),
            (_MUHURTA_ASTRONOMY, 'MU_SARVARTHA'),
        ],
    },
    'hora_tables': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/personal/lagna_hora.py', '_HORA_LORDS'),
            ('src/panels/today.ts', 'HORA_LORDS'),
        ],
    },
    'homa_election': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/personal/homa.py', 'HOMAHUTI_GROUP_LORDS'),
            (_MUHURTA_ASTRONOMY, 'MU_HOMAHUTI_LORDS'),
        ],
    },
    'named_shani_conditions': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/gochara/rules.py', 'named_conditions'),
            ('src/shani-conditions.ts', 'shaniConditionFromMoonHouse'),
        ],
    },
}


def _engine_asymmetry(snapshot: SourceSnapshot) -> dict[str, Any]:
    classes = {
        'PanchangamEngine': 'telugu_panchangam/engines/base.py',
        'DrikGanitaEngine': 'telugu_panchangam/engines/drik.py',
        'SuryaSiddhantaEngine': 'telugu_panchangam/engines/surya_siddhanta.py',
        'VakyaEngine': 'telugu_panchangam/engines/vakya.py',
    }
    result: dict[str, Any] = {}
    for class_name, path in classes.items():
        tree = ast.parse(snapshot.read(path), filename=path)
        node = next(
            item for item in tree.body
            if isinstance(item, ast.ClassDef) and item.name == class_name
        )
        result[class_name] = {
            'path': path,
            'bases': [ast.unparse(base) for base in node.bases],
            'defined_methods': sorted(
                item.name for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ),
        }
    concrete = [
        set(result[name]['defined_methods'])
        for name in ('DrikGanitaEngine', 'SuryaSiddhantaEngine', 'VakyaEngine')
    ]
    result['shared_method_names'] = {
        'all_three': sorted(set.intersection(*concrete)),
        'drik_and_surya_siddhanta': sorted(concrete[0] & concrete[1]),
        'surya_siddhanta_and_vakya': sorted(concrete[1] & concrete[2]),
    }
    return result


def _duplicate_contracts(snapshot: SourceSnapshot) -> list[dict]:
    groups = []
    for name, config in _DUPLICATE_CONTRACTS.items():
        locations = []
        strategy = config['strategy']
        for path, symbol in config['locations']:
            content = snapshot.read(path)
            if 'import sharedTables from ' in content:
                strategy = 'generated-from-python'
            line = _symbol_line(content, symbol)
            locations.append({'path': path, 'symbol': symbol, 'line': line})
        groups.append({
            'name': name,
            'strategy': strategy,
            'locations': locations,
        })
    return groups


def symbol_pattern(symbol: str) -> re.Pattern:
    if not symbol.isidentifier():
        return re.compile(re.escape(symbol))
    return re.compile(
        rf'^\s*(?:(?:export\s+)?(?:def|function|class)\s+'
        rf'{re.escape(symbol)}\b|(?:export\s+)?'
        rf'(?:(?:const|let|var)\s+)?{re.escape(symbol)}\b\s*[:=])'
    )


def _symbol_line(content: str, symbol: str) -> int | None:
    pattern = symbol_pattern(symbol)
    return next(
        (index for index, text in enumerate(content.splitlines(), 1)
         if pattern.search(text)),
        None,
    )
