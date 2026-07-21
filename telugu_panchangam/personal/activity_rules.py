# Activity rules — declarative per-activity configuration consumed by the
# muhurta scorer. Each entry describes what a given activity wants or avoids;
# the scorer reads these and applies bonuses/skips accordingly.
#
# Fields:
#   label                   human-readable name (MCP errors, UI dropdown)
#   skip_on_yoga            day omitted if any of these special yogas are active
#   skip_on_sankramana      omit slots overlapping the 16+16 ghati sankramana window
#   skip_on_khar_maasa      omit when Sun is in Dhanu or Meena
#   skip_on_adhika          omit during intercalary (Adhika) months
#   skip_on_pitru_paksha    omit during Bhadrapada Krishna paksha
#   skip_on_simha_stha_guru hard-skip for wedding while Jupiter is in Simha
#   penalty_on_simha_stha_shukra  soft score penalty when Venus is in Simha
#   skip_on_combust         list of planets ['Guru', 'Shukra'] — skip if combust
#   skip_on_panchaka_nakshatra   skip when day nakshatra is a Panchaka nakshatra
#   prefer_choghadiya       (block_name, bonus) — bonus when slot's block matches
#   prefer_tithi_class      Nanda|Bhadra|Jaya|Rikta|Purna — +1 when tithi matches
#   prefer_vara             list of vaaram names — +1 on matching weekday
#   prefer_lagna_class      Sthira|Chara|Dvisvabhava — +1 when rising sign matches
#   required_lagna_class    slot omitted unless its active Lagna matches
#   allowed_maasams         day omitted unless its normalized lunar month is listed
#   allowed_varas           day omitted unless its sunrise weekday is listed
#   avoid_vara_paksha       (Vara, Paksha) pairs that omit a day
#   allowed_solar_classes   day omitted unless Surya's Rasi is in one of these classes
#   allowed_nakshatras      slot omitted unless its active Nakshatra is listed
#   prefer_nakshatras       active Nakshatra names receiving +1
#   allowed_tithi_numbers   slot omitted unless its active Tithi number is listed
#   avoid_tithi_numbers     slot omitted when its active Tithi number is listed
#   allowed_lagnas          slot omitted unless its active Lagna is listed
#   caution_lagna_solar     disclose when the active Lagna equals Surya's Rasi
#   manual_checks           source-required criteria not computed by the finder
#   source_claim            stable verified claim ID in provenance.json
#   daytime_only            night_slots returns no candidates for the activity
#   prefer_bhadra_puchha    bonus when slot overlaps Bhadra Puchha
#   prefer_nakshatra_mukha  ([classes], bonus) — bonus when day nakshatra mukha matches
#   avoid_karana            karana names — slots overlapping these are cut

_SAMSKARA_SKIP = ('Visha Yoga', 'Dagdha Yoga')

ACTIVITY_RULES: dict[str, dict] = {
    # — Generic —
    'any':           {'label': 'Anything auspicious'},
    'travel':        {'label': 'Travel / journey',
                      'avoid_karana': ['Vishti'],
                      'prefer_lagna_class': 'Chara',
                      'prefer_nakshatra_mukha': (['Tiryan'], 1)},
    'purchase':      {'label': 'Purchase (general)',
                      'prefer_choghadiya': ('Labh', 1)},
    'ceremony':      {'label': 'Ceremony / puja (general)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_vara': ['Somavaram', 'Guruvaram'],
                      'avoid_tithi_class': ['Jaya']},
    'beginning':     {'label': 'New beginning (general)',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram', 'Guruvaram']},
    # — Samskaras —
    'wedding':       {'label': 'Wedding (Vivaha)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'skip_on_simha_stha_guru': True,
                      'penalty_on_simha_stha_shukra': -2,
                      'skip_on_combust': ['Guru', 'Shukra'],
                      'prefer_tithi_class': 'Purna',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Guruvaram', 'Somavaram'],
                      'prefer_lagna_class': 'Sthira'},
    'engagement':    {'label': 'Engagement (Nischayam)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_tithi_class': 'Purna',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Guruvaram', 'Somavaram'],
                      'prefer_lagna_class': 'Sthira'},
    'naming':        {'label': 'Naming (Namakaranam)',
                      'source_claim': 'muhurta.namakarana',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_choghadiya': ('Shubh', 1),
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_nakshatras': [
                          'Anuradha', 'Punarvasu', 'Magha',
                          'Uttara Phalguni', 'Uttara Ashadha',
                          'Uttara Bhadrapada', 'Shatabhisha', 'Swati',
                          'Dhanishtha', 'Shravana', 'Rohini', 'Ashwini',
                          'Mrigashira', 'Revati', 'Hasta', 'Pushya',
                      ],
                      'avoid_tithi_numbers': [4, 6, 8, 9, 12, 14, 15],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Prefer the 10th, 12th or 16th day after birth; '
                          'otherwise elect an auspicious day.',
                          'Election chart: strengthen Lagna and leave the '
                          '8th house unoccupied.',
                          'A common Lagna is acceptable only when occupied '
                          'by benefics.',
                          'Prefer Guru in a Kendra or Trikona with a malefic '
                          'in the 11th.',
                          'Alternative chart: benefic-sign Lagna, malefic in '
                          'the 3rd, Shukra in the 12th and Chandra dignified.',
                          'Choose a name appropriate to the ruling Nakshatra.',
                      ]},
    'annaprasana':   {'label': 'Annaprasana (First feeding)',
                      'source_claim': 'muhurta.annaprasana',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_choghadiya': ('Shubh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'avoid_tithi_class': ['Jaya'],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_nakshatras': [
                          'Ashwini', 'Mrigashira', 'Punarvasu',
                          'Dhanishtha', 'Pushya', 'Hasta', 'Swati',
                          'Anuradha', 'Shravana', 'Shatabhisha',
                          'Uttara Phalguni', 'Chitra',
                      ],
                      'avoid_tithi_numbers': [4, 6, 8, 12, 14, 15],
                      'allowed_lagnas': [
                          'Vrishabha', 'Mithuna', 'Karka', 'Simha',
                          'Kanya', 'Tula', 'Dhanu', 'Makara', 'Kumbha',
                      ],
                      'manual_checks': [
                          'Perform first feeding in the child’s 6th, 8th, '
                          '9th or 12th month; the age-month is the most '
                          'important criterion.',
                          'Election chart: leave the 10th house unoccupied.',
                          'Budha, Mangala and Shukra should not occupy the '
                          '7th, 8th and 9th houses respectively.',
                          'Budha, Guru or Shukra in Lagna is highly '
                          'commended; no malefic should occupy Lagna.',
                      ]},
    'karnavedha':    {'label': 'Karnavedha (Ear-piercing)',
                      'source_claim': 'muhurta.karnavedha',
                      'daytime_only': True,
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_tithi_class': 'Bhadra',
                      'avoid_tithi_class': ['Jaya'],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'avoid_tithi_numbers': [4, 6, 8, 12, 14, 15],
                      'allowed_lagnas': [
                          'Mesha', 'Vrishabha', 'Mithuna', 'Karka',
                          'Kanya', 'Tula', 'Dhanu', 'Makara', 'Meena',
                      ],
                      'manual_checks': [
                          'Perform on the 12th or 16th day after birth, or '
                          'in the child’s 6th, 7th or 8th month.',
                          'Reject a day on which two Nakshatras or two Tithis '
                          'rule during the ceremony period.',
                          'Election chart: leave the 8th house unoccupied.',
                      ]},
    'mundana':       {'label': 'Mundana / Chaula (First head-shave)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Budhavaram', 'Guruvaram'],
                      'prefer_lagna_class': 'Dvisvabhava'},
    'upanayana':     {'label': 'Upanayana (Sacred thread)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'skip_on_combust': ['Guru', 'Shukra'],
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Budhavaram', 'Guruvaram'],
                      'prefer_lagna_class': 'Dvisvabhava'},
    'vidyarambha':   {'label': 'Education start (Vidyarambha)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Budhavaram'],
                      'prefer_lagna_class': 'Dvisvabhava'},
    'gruhapravesha': {'label': 'Gruhapravesha (Home entry)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_tithi_class': 'Bhadra',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Guruvaram', 'Somavaram'],
                      'prefer_lagna_class': 'Sthira'},
    # — Acquisitions —
    'vehicle':       {'label': 'Vehicle purchase',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Shukravaram'],
                      'prefer_lagna_class': 'Sthira'},
    'property':      {'label': 'Land purchase (for building)',
                      'source_claim': 'muhurta.land_purchase.building',
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shanivaram',
                      ],
                      'allowed_nakshatras': [
                          'Ashwini', 'Rohini', 'Mrigashira', 'Punarvasu',
                          'Pushya', 'Uttara Phalguni', 'Hasta', 'Swati',
                          'Anuradha', 'Uttara Ashadha', 'Shravana',
                          'Dhanishtha', 'Shatabhisha',
                          'Uttara Bhadrapada',
                      ],
                      'avoid_tithi_numbers': [4, 9, 14],
                      'prefer_vara': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shanivaram',
                      ],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Election chart: the weekday lord should '
                          'preferably occupy Lagna.',
                          'Election chart: Guru should occupy a Kendra '
                          'or Trikona.',
                          'Election chart: Mangala should occupy the 11th '
                          'and not Lagna.',
                          'Election chart: Lagna and 7th lords should be '
                          'harmonious; avoid the 11th lord in the 12th.',
                      ]},
    'gold':          {'label': 'Gold / Jewelry purchase',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Shukravaram', 'Guruvaram'],
                      'prefer_lagna_class': 'Sthira'},
    # — Construction & Ventures —
    'bhumi_puja':    {'label': 'Bhumi Puja / Foundation laying',
                      'source_claim': 'muhurta.bhumi_puja.foundation',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'allowed_maasams': [
                          'Chaitra', 'Vaishakha', 'Shravana', 'Kartika',
                          'Magha',
                      ],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'avoid_vara_paksha': [('Somavaram', 'Krishna')],
                      'allowed_solar_classes': ['Sthira', 'Chara'],
                      'allowed_nakshatras': [
                          'Rohini', 'Mrigashira', 'Chitra', 'Hasta',
                          'Jyeshtha', 'Uttara Phalguni', 'Uttara Ashadha',
                          'Shravana', 'Swati', 'Pushya', 'Anuradha',
                          'Ashwini', 'Shatabhisha', 'Uttara Bhadrapada',
                          'Revati',
                      ],
                      'prefer_nakshatras': [
                          'Rohini', 'Mrigashira', 'Chitra', 'Hasta',
                          'Jyeshtha', 'Uttara Phalguni', 'Uttara Ashadha',
                          'Shravana',
                      ],
                      'allowed_tithi_numbers': [1, 2, 3, 5, 6, 7, 10, 11, 13, 15],
                      'prefer_vara': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'required_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Election chart: 8th house from Lagna must be vacant and free of malefic aspect.',
                          'Election chart: malefics should occupy 3rd, 6th or 11th; benefics should fortify Kendras and Trikonas.',
                          'Site ritual: after Puja, the first foundation stone is placed at the north-eastern corner.',
                      ]},
    'business':      {'label': 'Business launch',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Guruvaram', 'Budhavaram'],
                      'prefer_lagna_class': 'Sthira'},
    'job':           {'label': 'Job start / Contract signing',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Guruvaram', 'Budhavaram'],
                      'prefer_lagna_class': 'Sthira'},
    # — Spiritual —
    'yajna':         {'label': 'Yajna / Homam',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Purna',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Guruvaram', 'Somavaram'],
                      'prefer_lagna_class': 'Sthira'},
    'pilgrimage':    {'label': 'Pilgrimage (Tirtha Yatra)',
                      'avoid_karana': ['Vishti'],
                      'prefer_lagna_class': 'Chara'},
    # — Civil & Medical —
    'court':         {'label': 'Court / legal matter',
                      'prefer_tithi_class': 'Jaya',
                      'avoid_tithi_class': ['Purna'],
                      'prefer_vara': ['Mangalavaram']},
    'litigation':    {'label': 'Litigation / contest',
                      'prefer_tithi_class': 'Jaya',
                      'avoid_tithi_class': ['Purna'],
                      'prefer_vara': ['Mangalavaram'],
                      'prefer_bhadra_puchha': 2},
    'surgery':       {'label': 'Surgery / medical procedure',
                      'avoid_karana': ['Vishti'],
                      'prefer_vara': ['Mangalavaram']},
    # — Panchaka-restricted activities —
    'cremation':         {'label': 'Cremation rites',
                          'skip_on_panchaka_nakshatra': True},
    'construction_roof': {'label': 'Roof-laying / construction milestone',
                          'skip_on_panchaka_nakshatra': True},
    'wood_cutting':      {'label': 'Wood-cutting',
                          'skip_on_panchaka_nakshatra': True},
    # — Specialized activities —
    'well_digging':      {'label': 'Well digging',
                          'source_claim': 'muhurta.well_digging',
                          'allowed_nakshatras': [
                              'Revati', 'Uttara Bhadrapada', 'Hasta',
                              'Anuradha', 'Magha', 'Shravana', 'Rohini',
                              'Pushya',
                          ],
                          'allowed_lagnas': [
                              'Meena', 'Karkataka', 'Makara',
                          ],
                          'caution_lagna_solar': True,
                          'manual_checks': [
                              'Election chart: Shukra and Chandra should '
                              'occupy Kendras.',
                              'For abundant sweet water, Chandra or Shukra '
                              'should occupy a Kendra in a full watery Rasi.',
                          ]},
    'coronation':        {'label': 'Coronation / title ceremony',
                          'skip_on_yoga': list(_SAMSKARA_SKIP),
                          'prefer_nakshatra_mukha': (['Urdhva'], 1)},
}

ACTIVITIES = tuple(ACTIVITY_RULES.keys())
