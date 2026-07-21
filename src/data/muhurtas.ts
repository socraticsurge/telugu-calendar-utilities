// Daytime named muhurtas — mirror of telugu_panchangam/muhurtas.py
// DAY_MUHURTAS (the source of record: docs/reference/07-muhurta-table.md).
// [name, deity ('' for concept-names), nature] in order 1..15 from sunrise.
// The website finder is daytime-only, so only the 15 day muhurtas are needed.
export const MUHURTA_DAY: [string, string, 'auspicious' | 'inauspicious'][] = [
  ['Rudra',       'Rudra (fierce Shiva)',    'inauspicious'],
  ['Ahi',         'Sarpa (the Serpent)',     'inauspicious'],
  ['Mitra',       'Mitra (Aditya)',          'auspicious'],
  ['Pitri',       'the Pitrs (ancestors)',   'inauspicious'],
  ['Vasu',        'the Vasus',               'auspicious'],
  ['Vara',        'Varaha (Vishnu)',         'auspicious'],
  ['Vishvedeva',  'the Vishvedevas',         'auspicious'],
  ['Vidhi',       'Brahma',                  'auspicious'],   // 8th = Abhijit (except Wed)
  ['Sathamukhi',  '',                        'auspicious'],
  ['Puruhuta',    'Indra',                   'inauspicious'],
  ['Vahini',      '',                        'inauspicious'],
  ['Naktanchara', '',                        'inauspicious'],
  ['Varuna',      'Varuna',                  'auspicious'],
  ['Aryama',      'Aryaman (Aditya)',        'auspicious'],
  ['Bhaga',       'Bhaga (Aditya)',          'inauspicious'],
];
