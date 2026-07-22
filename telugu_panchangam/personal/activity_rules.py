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
#   allowed_maasa_solar_pairs  additional exact (Maasa, Surya-Rasi) admissions
#   allowed_varas           day omitted unless its sunrise weekday is listed
#   avoid_vara_paksha       (Vara, Paksha) pairs that omit a day
#   allowed_solar_classes   day omitted unless Surya's Rasi is in one of these classes
#   allowed_nakshatras      slot omitted unless its active Nakshatra is listed
#   avoid_nakshatras        slot omitted when its active Nakshatra is listed
#   prefer_nakshatras       active Nakshatra names receiving +1
#   allowed_tithi_numbers   slot omitted unless its active Tithi number is listed
#   prefer_tithi_numbers    named source-favoured Tithis receive a bonus
#   avoid_tithi_numbers     slot omitted when its active Tithi number is listed
#   allowed_lagnas          slot omitted unless its active Lagna is listed
#   prefer_lagnas           named source-favoured Lagnas receive a bonus
#   caution_lagna_solar     disclose when the active Lagna equals Surya's Rasi
#   manual_checks           source-required criteria not computed by the finder
#   manual_prerequisites    unresolved checks cap relative tier below Excellent
#   avoid_janma_nakshatra   slot omitted when its star matches a supplied Janma star
#   avoid_vara_tithi_names  slot omitted for exact (Vara, Tithi-name) pairs
#   avoid_nitya_yogas       slot omitted while one of these Nitya Yogas is active
#   audit_claim             provenance claim recording a known evidence conflict;
#                           never grants verified status
#   heuristic_claim         provenance claim recording intentionally project-defined
#                           or source-neutral behavior; never grants verified status
#   related_claims          additional provenance claims (including lineage conflicts)
#                           relevant to the profile but not its implementation authority
#   source_claim            stable verified claim ID in provenance.json
#   daytime_only            night_slots returns no candidates for the activity
#   forenoon_only           candidate must end by local solar noon
#   allowed_pakshams        day omitted unless its Paksha is listed
#   allowed_solar_signs     day omitted unless Surya's Rasi is listed
#   allowed_tithi_names     exact Paksha-qualified Tithis admitted at slot time
#   prefer_bhadra_puchha    bonus when slot overlaps Bhadra Puchha
#   prefer_nakshatra_mukha  ([classes], bonus) — bonus when day nakshatra mukha matches
#   avoid_karana            karana names — slots overlapping these are cut

_SAMSKARA_SKIP = ('Visha Yoga', 'Dagdha Yoga')

# Source literature and practitioner-facing labels commonly use Ashwini and
# Moola, while the engine's canonical name table uses Ashvini and Mula. Keep
# source-facing rule text stable, but normalize before comparisons.
_NAKSHATRA_ALIASES = {
    'Ashwini': 'Ashvini',
    'Moola': 'Mula',
}


def canonical_activity_nakshatra(name: str) -> str:
    """Return the engine-canonical spelling for an activity-rule star."""
    return _NAKSHATRA_ALIASES.get(name, name)


def canonical_activity_nakshatras(names) -> frozenset[str]:
    """Normalize a configured Nakshatra collection for scorer membership."""
    return frozenset(canonical_activity_nakshatra(name) for name in names)

ACTIVITY_RULES: dict[str, dict] = {
    # — Generic —
    'any':           {'label': 'Anything auspicious',
                      'heuristic_claim': 'muhurta.any.shared_scoring'},
    'travel':        {'label': 'Travel / journey',
                      'source_claim': 'muhurta.travel',
                      'avoid_karana': ['Vishti'],
                      'avoid_nakshatras': ['Bharani', 'Krittika'],
                      'prefer_nakshatras': [
                          'Mrigashira', 'Ashwini', 'Pushya', 'Punarvasu',
                          'Hasta', 'Anuradha', 'Shravana', 'Moola',
                          'Dhanishtha', 'Revati',
                      ],
                      'prefer_lagna_class': 'Chara',
                      'prefer_nakshatra_mukha': (['Tiryan'], 1),
                      'manual_checks': [
                          'Election chart: fortify Lagna; Guru or Shukra '
                          'well placed in Lagna is stated to support a '
                          'successful journey.',
                          'For long-distance journeys, prefer waxing '
                          'Chandra, avoid Mangala in the 8th and avoid '
                          'malefics in the 7th.',
                      ]},
    'purchase':      {'label': 'Purchase (general)',
                      'source_claim': 'muhurta.purchase.general',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_nakshatras': [
                          'Revati', 'Shatabhisha', 'Ashwini', 'Swati',
                          'Shravana', 'Chitra',
                      ],
                      'manual_checks': [
                          'Transaction role: verse 16 distinguishes purchase '
                          'from sale Muhurtas; this profile evaluates the '
                          'buyer’s side and must not be reused as a seller '
                          'election.',
                          'Marketplace check from verse 17: avoid Rikta '
                          'Tithis, Tuesday and Kumbha Lagna; prefer Chandra '
                          'and Shukra in Lagna, no malefics in the 8th or '
                          '12th, and benefics in the 2nd, 10th or 11th.',
                          'Use the dedicated vehicle, building-land or gold '
                          'profile when the object is known; their narrower '
                          'rules take precedence over generic purchase.',
                      ]},
    'business_inventory_purchase': {
                      'label': 'Trade inventory purchase',
                      'source_claim': 'muhurta.trade_inventory.purchase',
                      'related_claims': ['muhurta.purchase.general'],
                      'manual_prerequisites': True,
                      'allowed_varas': [
                          'Adivaram', 'Somavaram', 'Budhavaram',
                          'Guruvaram', 'Shukravaram', 'Shanivaram',
                      ],
                      'prefer_vara': ['Guruvaram'],
                      'prefer_tithi_numbers': [10],
                      'prefer_nakshatras': ['Pushya'],
                      'manual_checks': [
                          'Transaction role: buying stock, raw materials or '
                          'goods for resale or business use; do not reuse '
                          'this profile for selling inventory, launching a '
                          'business or deploying capital.',
                          'Saturday is described as passable, not preferred.',
                          'Election chart: Budha, the 2nd lord and the 2nd '
                          'house should be fortified.',
                          'Election chart: avoid Budha afflicted by Mangala; '
                          'Budha and Guru together in Lagna or in mutual '
                          'aspect are described as highly favourable.',
                          'Commercial need, stock quality, supplier terms, '
                          'cash flow, tax and legal advice take precedence '
                          'over electional timing.',
                      ]},
    'borrowing_money': {
                      'label': 'Borrowing money / taking a loan',
                      'source_claim': 'muhurta.borrowing_money',
                      'related_claims': [
                          'muhurta.borrowing.chintamani_divergence'],
                      'manual_prerequisites': True,
                      'avoid_nakshatras': [
                          'Krittika', 'Moola', 'Punarvasu', 'Dhanishtha',
                      ],
                      'avoid_janma_nakshatra': True,
                      'manual_checks': [
                          'Transaction role: this is the borrower/debtor '
                          'side only; do not reuse it for lending, receiving '
                          'repayment or deploying capital.',
                          'Personal-star gate: supply every borrower’s Janma '
                          'Nakshatra so the source prohibition can be '
                          'enforced; without it, review remains incomplete.',
                          'Election chart: avoid Chandra conjoined with '
                          'Mangala or Shani.',
                          'Purpose-specific chart: for quick domestic or '
                          'personal use, Chandra should favour Lagna; for '
                          'business use, Chandra should favour Budha and the '
                          'Lagna lord.',
                          'Repayment capacity, total borrowing cost, lender '
                          'terms, collateral risk and qualified financial or '
                          'legal advice take precedence over timing.',
                      ]},
    'lending_money': {'label': 'Lending money / giving a loan',
                      'source_claim': 'muhurta.lending_money',
                      'related_claims': [
                          'muhurta.lending.drkpanchang_divergence'],
                      'manual_prerequisites': True,
                      'allowed_varas': [
                          'Adivaram', 'Somavaram', 'Budhavaram',
                          'Guruvaram', 'Shanivaram',
                      ],
                      'avoid_nakshatras': [
                          'Krittika', 'Magha', 'Moola', 'Shatabhisha',
                          'Uttara Phalguni', 'Punarvasu',
                      ],
                      'avoid_janma_nakshatra': True,
                      'avoid_vara_tithi_names': [
                          ['Shanivaram', 'Amavasya'],
                      ],
                      'manual_checks': [
                          'Transaction role: this is making a loan from the '
                          'lender/creditor side; receiving repayment and '
                          'borrowing money are separate elections.',
                          'Personal-star gate: supply the lender’s Janma '
                          'Nakshatra so the source prohibition can be '
                          'enforced; without it, review remains incomplete.',
                          'Election chart: Lagna and 7th lords should be '
                          'harmoniously disposed.',
                          'Election chart: Chandra in Vrischika is described '
                          'as adverse for the lender.',
                          'Lineage warning: current Drik Panchang loan-giving '
                          'practice excludes Wednesday, while this Raman-'
                          'lineage profile admits it and excludes Tuesday '
                          'and Friday.',
                          'Credit assessment, affordability, documentation, '
                          'interest and collateral law, concentration risk '
                          'and qualified financial or legal advice take '
                          'precedence over timing.',
                      ]},
    'ceremony':      {'label': 'Ceremony / puja (general)',
                      'audit_claim': 'muhurta.ceremony.profile_conflict',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_vara': ['Somavaram', 'Guruvaram'],
                      'avoid_tithi_class': ['Jaya'],
                      'manual_checks': [
                          'Shantika/Paushtika cross-check: Muhurta '
                          'Chintamani verse 34 rejects Rikta Tithis, '
                          'Ashtami, Pournami and Amavasya—not the '
                          'configured Jaya family.',
                          'For the cited rites, use Ashwini, Pushya, Hasta, '
                          'the three Uttaras, Rohini, Revati, Shravana, '
                          'Dhanishtha, Shatabhisha, Punarvasu, Swati, '
                          'Anuradha or Magha; reject Sunday, Tuesday and '
                          'Saturday; place Surya in the 10th, Chandra in '
                          'the 4th and Guru in Lagna.',
                          'Scope warning: verse 34 concerns Shantika and '
                          'Paushtika rites, not every ceremony or Puja; '
                          'emergency Shanti for an ominous event may relax '
                          'ordinary timing restrictions.',
                      ]},
    'beginning':     {'label': 'New beginning (general)',
                      'audit_claim': 'muhurta.beginning.profile_conflict',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram', 'Guruvaram'],
                      'manual_checks': [
                          'Dharma-work cross-check: Muhurta Chintamani '
                          'verse 30 names Anuradha, Ashwini, Pushya, Hasta, '
                          'Shravana, Dhanishtha, Shatabhisha, Punarvasu, '
                          'Swati, the three Uttaras and Rohini; Sunday '
                          'through Friday except Tuesday.',
                          'Election chart for beginning Dharma-kriya: use '
                          'Budha or Guru Lagna/varga, place Guru in Lagna '
                          'and ensure the performer has Guru-bala.',
                          'Scope warning: the passage begins Dharma-kriya, '
                          'not every modern project or life change; it does '
                          'not supply the configured Amrit Choghadiya or '
                          'Nanda-Tithi rewards.',
                      ]},
    # — Samskaras —
    'wedding':       {'label': 'Wedding (Vivaha)',
                      'source_claim': 'muhurta.wedding',
                      'related_claims': [
                          'muhurta.wedding.drkpanchang_divergence'],
                      'manual_prerequisites': True,
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'skip_on_simha_stha_guru': True,
                      'penalty_on_simha_stha_shukra': -2,
                      'skip_on_combust': ['Guru', 'Shukra'],
                      'allowed_maasams': [
                          'Magha', 'Phalguna', 'Vaishakha', 'Jyeshtha',
                          'Kartika', 'Margashira',
                      ],
                      'allowed_maasa_solar_pairs': [
                          ['Pushya', 'Makara'], ['Chaitra', 'Mesha'],
                      ],
                      'allowed_varas': [
                          'Adivaram', 'Somavaram', 'Budhavaram',
                          'Guruvaram', 'Shukravaram', 'Shanivaram',
                      ],
                      'prefer_vara': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_tithi_names': [
                          'Shukla Pratipat', 'Shukla Dwitiya',
                          'Shukla Tritiya', 'Shukla Panchami',
                          'Shukla Saptami', 'Shukla Dashami',
                          'Shukla Ekadashi', 'Shukla Trayodashi',
                          'Krishna Pratipat', 'Krishna Dwitiya',
                          'Krishna Tritiya', 'Krishna Panchami',
                          'Krishna Saptami', 'Krishna Dashami',
                      ],
                      'allowed_nakshatras': [
                          'Rohini', 'Mrigashira', 'Magha',
                          'Uttara Phalguni', 'Hasta', 'Swati', 'Anuradha',
                          'Moola', 'Uttara Ashadha',
                          'Uttara Bhadrapada', 'Revati',
                      ],
                      'avoid_karana': ['Vishti'],
                      'avoid_nitya_yogas': [
                          'Vyatipata', 'Dhruva', 'Ganda', 'Vajra',
                          'Shoola', 'Vishkambha', 'Atiganda', 'Vyaghata',
                          'Parigha',
                      ],
                      'allowed_lagnas': [
                          'Mithuna', 'Kanya', 'Tula', 'Vrishabha',
                          'Karka', 'Simha', 'Dhanu', 'Kumbha',
                      ],
                      'prefer_lagnas': ['Mithuna', 'Kanya', 'Tula'],
                      'manual_checks': [
                          'Nakshatra Pada gate: reject Magha and Moola Pada '
                          '1 and Revati Pada 4. Pada is not computed across '
                          'every surface, so the automated profile admits the '
                          'star only subject to this mandatory check.',
                          'Yoga vocabulary: Raman also rejects a named '
                          'Mrityu Yoga that is not one of the engine’s 27 '
                          'Nitya Yogas; verify the applicable lineage '
                          'definition manually.',
                          'Election chart: keep the 7th house unoccupied; '
                          'Mangala out of the 8th; Shukra out of the 6th; '
                          'Lagna free from malefics and not hemmed between '
                          'them; and Chandra unassociated with another Graha.',
                          'Fortification: consider Guru, Budha or Shukra in '
                          'Lagna and malefics in the 3rd or 11th, or one of '
                          'the source’s named marriage-election Yogas.',
                          'Couple-specific prerequisites: complete horoscope '
                          'compatibility review, Tarabala, Chandrabala and '
                          'Panchaka review for both partners; an election '
                          'cannot substitute for consent or relationship '
                          'judgment.',
                          'Lineage warning: current Drik Panchang Hyderabad '
                          'dates admit some Tuesdays and Tithis Raman rejects. '
                          'This profile follows Raman’s named method rather '
                          'than silently blending published practices.',
                      ]},
    'engagement':    {'label': 'Engagement (Nischayam)',
                      'audit_claim': 'muhurta.engagement.profile_conflict',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_tithi_class': 'Purna',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Guruvaram', 'Somavaram'],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Scope warning: the inspected Raman edition has no '
                          'dedicated Betrothal or Nischayam election; do not '
                          'silently treat marriage rules as engagement rules.',
                          'If the marriage passage is used as a conservative '
                          'cross-check, verify its exact Tithi, weekday, '
                          'Nakshatra and rising-Rasi gates; this profile does '
                          'not implement them.',
                      ]},
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
                      'source_claim': 'muhurta.mundana',
                      'forenoon_only': True,
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'skip_on_combust': ['Guru', 'Shukra'],
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'allowed_pakshams': ['Shukla'],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_tithi_numbers': [2, 3, 5, 7, 10, 11, 13],
                      'allowed_nakshatras': [
                          'Punarvasu', 'Mrigashira', 'Dhanishtha',
                          'Shravana', 'Revati', 'Pushya', 'Chitra',
                          'Ashwini', 'Hasta', 'Swati', 'Rohini',
                          'Shatabhisha', 'Uttara Phalguni',
                          'Uttara Bhadrapada', 'Uttara Ashadha',
                      ],
                      'prefer_nakshatras': [
                          'Punarvasu', 'Mrigashira', 'Dhanishtha',
                          'Shravana', 'Revati', 'Pushya', 'Chitra',
                          'Ashwini', 'Hasta',
                      ],
                      'allowed_lagnas': [
                          'Karka', 'Kanya', 'Mithuna', 'Meena', 'Tula',
                          'Vrishabha', 'Makara',
                      ],
                      'manual_checks': [
                          'Perform in the child’s 3rd or 5th year, and not '
                          'while the child’s mother is pregnant.',
                          'Confirm the source’s stated Surya-in-Karkataka '
                          'seasonal condition with the officiating astrologer.',
                          'Other rising Rasis require a strong benefic in '
                          'Lagna; Kumbha must still be rejected.',
                          'Election chart: place benefics in the 4th, 5th, '
                          '7th, 9th, 10th and 11th; malefics in the 3rd, '
                          '6th and 11th.',
                          'Leave the 8th house unoccupied and avoid Surya, '
                          'Mangala or preferably any malefic in the 7th.',
                      ]},
    'upanayana':     {'label': 'Upanayana (Sacred thread)',
                      'source_claim': 'muhurta.upanayana',
                      'forenoon_only': True,
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'allowed_maasams': [
                          'Magha', 'Phalguna', 'Chaitra', 'Vaishakha',
                      ],
                      'allowed_solar_signs': [
                          'Makara', 'Kumbha', 'Meena', 'Mesha',
                          'Vrishabha', 'Mithuna',
                      ],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_tithi_names': [
                          'Shukla Dwitiya', 'Shukla Tritiya',
                          'Shukla Panchami', 'Shukla Saptami',
                          'Shukla Dashami', 'Shukla Trayodashi',
                          'Krishna Pratipat', 'Krishna Dwitiya',
                          'Krishna Tritiya',
                      ],
                      'allowed_nakshatras': [
                          'Anuradha', 'Hasta', 'Chitra', 'Swati',
                          'Shravana', 'Dhanishtha', 'Shatabhisha',
                          'Uttara Phalguni', 'Uttara Ashadha',
                          'Uttara Bhadrapada', 'Revati', 'Rohini',
                          'Mrigashira', 'Ashwini', 'Punarvasu', 'Pushya',
                      ],
                      'allowed_lagnas': [
                          'Mesha', 'Vrishabha', 'Mithuna', 'Karka',
                          'Kanya', 'Tula', 'Kumbha',
                      ],
                      'manual_checks': [
                          'Perform in the 5th or 8th year; if delayed, '
                          'apply the source’s age limits and exception rules.',
                          'Reject Wednesday when Budha is combust.',
                          'Chandra must not occupy the 6th, 8th or 12th from '
                          'Lagna; avoid malefics in Kendras.',
                          'Leave the 8th house unoccupied; fortify the 3rd '
                          'and keep the 6th free of a benefic.',
                          'Avoid Mangala and Shani in the 2nd, 5th or 12th.',
                          'Avoid Chandra in Lagna except the source’s stated '
                          'Karka-Lagna Guru conjunction exception.',
                          'Review the named adverse and favorable election '
                          'Yogas listed in the remainder of the passage.',
                      ]},
    'vidyarambha':   {'label': 'Education start (Vidyarambha)',
                      'source_claim': 'muhurta.vidyarambha',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'skip_on_sankramana': True,
                      'skip_on_khar_maasa': True,
                      'skip_on_adhika': True,
                      'skip_on_pitru_paksha': True,
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'avoid_tithi_class': ['Jaya'],
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_nakshatras': [
                          'Ashwini', 'Punarvasu', 'Ardra', 'Hasta',
                          'Chitra', 'Swati', 'Shravana', 'Revati',
                      ],
                      'allowed_lagnas': [
                          'Mesha', 'Karka', 'Tula', 'Makara',
                          'Mithuna', 'Kanya', 'Dhanu', 'Meena',
                      ],
                      'manual_checks': [
                          'The source’s most propitious age marker is the '
                          '5th day of the 5th month of the child’s 5th year.',
                          'Prefer the forenoon or noon for the ceremony.',
                          'Election chart: leave the 8th house unoccupied.',
                          'Budha, Shukra and Guru together in the 9th are '
                          'stated to counteract adverse influences.',
                      ]},
    'seemantha':     {'label': 'Seemantha (Prenatal ceremony)',
                      'source_claim': 'muhurta.seemantha',
                      'related_claims': [
                          'muhurta.seemantha.chintamani_divergence',
                      ],
                      'manual_prerequisites': True,
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_nakshatras': [
                          'Rohini', 'Mrigashira', 'Punarvasu', 'Pushya',
                          'Uttara Phalguni', 'Uttara Ashadha', 'Hasta',
                          'Shravana', 'Revati',
                      ],
                      'allowed_tithi_names': [
                          'Shukla Pratipat', 'Shukla Dwitiya',
                          'Shukla Tritiya', 'Shukla Panchami',
                          'Shukla Saptami', 'Shukla Dashami',
                          'Shukla Ekadashi', 'Shukla Dwadashi',
                          'Shukla Trayodashi', 'Krishna Pratipat',
                          'Krishna Dwitiya', 'Krishna Tritiya',
                          'Krishna Panchami', 'Krishna Saptami',
                          'Krishna Dashami', 'Krishna Ekadashi',
                          'Krishna Dwadashi', 'Krishna Trayodashi',
                      ],
                      'allowed_lagnas': [
                          'Mesha', 'Vrishabha', 'Mithuna', 'Karka',
                          'Kanya', 'Tula', 'Dhanu', 'Makara', 'Kumbha',
                          'Meena',
                      ],
                      'manual_checks': [
                          'Pregnancy timing: the cited passage ordains '
                          'Seemantha for the first pregnancy, in the 5th or '
                          '7th month; if that schedule is missed, perform it '
                          'before delivery under practitioner guidance. '
                          'Muhurta Chintamani verse 8 instead specifies the '
                          '6th or 8th month; choose the family’s tradition '
                          'with a qualified practitioner.',
                          'Under unavoidable circumstances, Ashwini, '
                          'Anuradha or Moola may be considered; the automated '
                          'profile admits only the primary Nakshatra list.',
                          'Pournami is admissible only when Chandra is '
                          'dignified; the automated profile conservatively '
                          'omits it pending chart judgment.',
                          'Election chart: leave the 8th house vacant and '
                          'do not place Chandra in the 8th.',
                          'Personal star check: avoid the 3rd, 7th, 8th, '
                          '10th and 22nd Nakshatras counted from the '
                          'mother’s birth Nakshatra.',
                          'The source makes the pregnancy month primary and '
                          'permits Guru or Shukra combustion to be ignored '
                          'for this rite; no combustion gate is applied.',
                          'Maternal comfort, clinician instructions and '
                          'medical care always take precedence over '
                          'electional timing.',
                      ]},
    'gruhapravesha': {'label': 'Gruhapravesha (First entry into new home)',
                      'source_claim': 'muhurta.gruhapravesha',
                      'related_claims': [
                          'muhurta.gruhapravesha.drkpanchang_divergence'],
                      'manual_prerequisites': True,
                      'allowed_varas': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                          'Shukravaram',
                      ],
                      'allowed_solar_signs': [
                          'Makara', 'Kumbha', 'Meena', 'Mesha',
                          'Vrishabha', 'Mithuna',
                      ],
                      'allowed_tithi_names': [
                          'Krishna Pratipat', 'Shukla Dwitiya',
                          'Shukla Tritiya', 'Shukla Panchami',
                          'Shukla Saptami', 'Shukla Dashami',
                          'Shukla Ekadashi', 'Shukla Trayodashi',
                      ],
                      'allowed_nakshatras': [
                          'Rohini', 'Mrigashira', 'Uttara Ashadha',
                          'Chitra', 'Uttara Bhadrapada', 'Anuradha',
                          'Revati',
                      ],
                      'allowed_lagnas': [
                          'Vrishabha', 'Simha', 'Vrischika', 'Kumbha',
                          'Mithuna', 'Kanya', 'Dhanu', 'Meena',
                      ],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Ritual scope: first ceremonial entry into a newly '
                          'built home only; buying a completed house, moving '
                          'rental, or re-entering after repairs are separate '
                          'elections.',
                          'Election chart: Guru, Shukra and Chandra should be '
                          'strong; leave the 8th house vacant, place malefics '
                          'in Upachayas and benefics in Kendras, and preferably '
                          'use a Guru- or Shukra-owned rising Rasi.',
                          'Lagna lineage: fixed Rasis are preferred and dual '
                          'Rasis are ordinary. Raman permits a movable Rasi '
                          'only with Vrishabha Navamsa; the automated profile '
                          'conservatively omits that uncomputed exception.',
                          'Personal and ritual checks: the owner’s Janma Rasi, '
                          'Nakshatra or Lagna may strengthen the election; '
                          'complete worship and Bhootabali before entry.',
                          'Pregnancy safety: Raman advises avoiding entry after '
                          'six months of the wife’s pregnancy. Maternal comfort, '
                          'clinician instructions and medical care always take '
                          'precedence over timing.',
                          'Lineage warning: current Drik Panchang practice also '
                          'admits some Saturdays and applies additional month '
                          'filters; this profile follows Raman’s four weekdays '
                          'rather than silently blending methodologies.',
                      ]},
    # — Acquisitions —
    'vehicle':       {'label': 'Vehicle purchase',
                      'source_claim': 'muhurta.vehicle.acquisition',
                      'prefer_nakshatras': [
                          'Shravana', 'Dhanishtha', 'Shatabhisha',
                          'Punarvasu', 'Swati',
                      ],
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
    'house_purchase': {
                      'label': 'Completed house purchase',
                      'source_claim': 'muhurta.house_purchase.completed',
                      'related_claims': ['muhurta.purchase.general'],
                      'manual_prerequisites': True,
                      'allowed_varas': ['Guruvaram', 'Shukravaram'],
                      'allowed_tithi_numbers': [1, 6, 11],
                      'allowed_nakshatras': [
                          'Mrigashira', 'Ashlesha', 'Magha',
                          'Purva Phalguni', 'Vishakha', 'Moola',
                          'Punarvasu', 'Revati',
                      ],
                      'prefer_lagnas': [
                          'Vrishabha', 'Mithuna', 'Simha', 'Tula',
                          'Vrischika',
                      ],
                      'manual_checks': [
                          'Scope: use this profile for buying a completed '
                          'new or old house; it is not land purchase, '
                          'construction commencement, rental moving or '
                          'Gruhapravesha.',
                          'Election chart: keep malefics out of the 7th '
                          'house.',
                          'Election chart: do not place Mangala in Lagna.',
                          'Legal title, structural inspection, financing and '
                          'contract advice take precedence over electional '
                          'timing.',
                      ]},
    'gold':          {'label': 'Gold / Jewelry purchase',
                      'source_claim': 'muhurta.gold_jewelry.purchase',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Shukravaram', 'Guruvaram'],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Election chart: Surya and Chandra should be well '
                          'situated and aspected; the cited passage leaves '
                          'this as a chart judgment rather than a fixed '
                          'weekday, Tithi, Nakshatra or Lagna list.',
                      ]},
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
    'home_repair':   {'label': 'Home repair / renovation start',
                      'source_claim': 'muhurta.home_repair.commencement',
                      'manual_prerequisites': True,
                      # Raman prohibits only Tuesday absolutely. Sunday and
                      # Saturday are admitted without a source-backed bonus.
                      'allowed_varas': [
                          'Adivaram', 'Somavaram', 'Budhavaram',
                          'Guruvaram', 'Shukravaram', 'Shanivaram',
                      ],
                      'prefer_vara': [
                          'Somavaram', 'Budhavaram', 'Guruvaram',
                      ],
                      'manual_checks': [
                          'Scope: commencement of repairs or renovation to '
                          'an existing home only; painting/whitewashing, '
                          'dismantling, new construction and post-work '
                          're-entry are separate elections.',
                          'Weekday-Lagna condition: Friday is especially '
                          'suitable with Vrishabha or Tula Lagna; Monday is '
                          'especially suitable with Karka Lagna.',
                          'Election chart: Lagna should be occupied by a '
                          'benefic and Chandra should be in an aquatic Rasi.',
                          'Mangala transit: if Chandra is in Krittika, Magha, '
                          'Pushya, Purva Phalguni, Hasta, Moola or Revati, '
                          'confirm Mangala is not transiting that same '
                          'Nakshatra.',
                          'Building permits, structural engineering, utility '
                          'safety and contractor readiness take precedence '
                          'over electional timing.',
                      ]},
    'business':      {'label': 'Business launch',
                      'audit_claim': 'muhurta.business.profile_conflict',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Guruvaram', 'Budhavaram'],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Capital-deployment cross-check: Muhurta '
                          'Chintamani verse 27 prefers Swati, Punarvasu, '
                          'Chitra, Anuradha, Mrigashira, Revati, Vishakha, '
                          'Pushya, Shravana, Dhanishtha, Shatabhisha and '
                          'Ashwini, with a Chara—not Sthira—Lagna.',
                          'Election chart for deploying funds: benefics in '
                          'the 5th and 9th and an unoccupied 8th house.',
                          'Scope warning: capital deployment, marketplace '
                          'trade and inventory purchase are distinct source '
                          'activities; none inspected is a universal modern '
                          'business-launch election.',
                      ]},
    'job':           {'label': 'Job start / Contract signing',
                      'audit_claim': 'muhurta.job_contract.profile_conflict',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Guruvaram', 'Budhavaram'],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'For entering service, Muhurta Chintamani verse '
                          '26 names Ashwini, Pushya, Hasta, Chitra, '
                          'Anuradha, Mrigashira and Revati; Wednesday, '
                          'Friday, Sunday and Thursday; a benefic in Lagna; '
                          'and Surya or Mangala in the 10th or 11th.',
                          'Employer/employee check: compare birth-Nakshatra '
                          'Yoni friendship and friendship between both '
                          'Janma-Rasi lords before entering service.',
                          'Contract warning: verse 42 concerns Sandhana '
                          '(peace, alliance or friendship), not a modern '
                          'employment or commercial contract; do not treat '
                          'it as direct authority for signing.',
                      ]},
    # — Spiritual —
    'yajna':         {'label': 'Yajna / Homam',
                      'audit_claim': 'muhurta.yajna.profile_conflict',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Purna',
                      'avoid_tithi_class': ['Jaya'],
                      'prefer_vara': ['Guruvaram', 'Somavaram'],
                      'prefer_lagna_class': 'Sthira',
                      'manual_checks': [
                          'Homahuti check: count the day’s Nakshatra from '
                          'Surya’s Nakshatra in three-star groups and reject '
                          'a group assigned to a malefic Graha, per Muhurta '
                          'Chintamani verse 35.',
                          'Agnivasa check: apply the Tithi-plus-weekday '
                          'modulo-four rule in verse 36; only remainders 3 '
                          'and 0 place Agni on earth and support Homa.',
                          'Ritual scope: a general Yajna is not necessarily '
                          'equivalent to the cited Homahuti election; follow '
                          'the officiating priest and the specific Kalpa or '
                          'Sampradaya requirements.',
                      ]},
    'pilgrimage':    {'label': 'Pilgrimage (Tirtha Yatra)',
                      'source_claim': 'muhurta.pilgrimage',
                      'avoid_karana': ['Vishti'],
                      'skip_on_combust': ['Guru'],
                      'avoid_tithi_numbers': [14, 15],
                      'prefer_nakshatras': [
                          'Mrigashira', 'Ashwini', 'Pushya', 'Punarvasu',
                          'Hasta', 'Anuradha', 'Shravana', 'Moola',
                          'Dhanishtha', 'Revati',
                      ],
                      'prefer_lagna_class': 'Chara',
                      'manual_checks': [
                          'Election chart: place Guru in Lagna or the 9th '
                          'house, as required by the pilgrimage-specific '
                          'passage.',
                      ]},
    # — Civil & Medical —
    'court':         {'label': 'Court / legal matter',
                      'audit_claim': 'muhurta.court.profile_conflict',
                      'prefer_tithi_class': 'Jaya',
                      'avoid_tithi_class': ['Purna'],
                      'prefer_vara': ['Mangalavaram'],
                      'manual_checks': [
                          'Known source mismatch: this profile rewards '
                          'Tuesday, but Raman rejects Tuesday and Saturday '
                          'for filing lawsuits; verify the exact Nakshatra '
                          'and weekday gates before acting.',
                          'Practitioner checks: Guru in a Trikona from a '
                          'strengthened Lagna; no malefic in the 6th; Lagna '
                          'and 6th lords separated; Mesha Lagna or Navamsa.',
                      ]},
    'litigation':    {'label': 'Litigation / contest',
                      'audit_claim': 'muhurta.litigation.profile_conflict',
                      'prefer_tithi_class': 'Jaya',
                      'avoid_tithi_class': ['Purna'],
                      'prefer_vara': ['Mangalavaram'],
                      'prefer_bhadra_puchha': 2,
                      'manual_checks': [
                          'Known source mismatch: this profile rewards '
                          'Tuesday, but Raman rejects Tuesday and Saturday '
                          'for filing lawsuits; verify the exact Nakshatra '
                          'and weekday gates before acting.',
                          'The Bhadra Puchha contest bonus is attributed to '
                          'Muhurta Chintamani and Dharma Sindhu but still '
                          'needs an edition-specific verse/page locator.',
                      ]},
    'surgery':       {'label': 'Surgery / medical procedure',
                      'source_claim': 'muhurta.surgery',
                      'avoid_karana': ['Vishti'],
                      'allowed_varas': ['Mangalavaram', 'Shanivaram'],
                      'allowed_tithi_names': [
                          'Shukla Chaturthi', 'Shukla Navami',
                          'Shukla Chaturdashi',
                      ],
                      'allowed_nakshatras': [
                          'Ardra', 'Jyeshtha', 'Ashlesha', 'Moola',
                      ],
                      'manual_checks': [
                          'Medical urgency and the treating clinician’s '
                          'instructions always override Muhurtam; never '
                          'delay necessary care for an astrological window.',
                          'Avoid Chandra in the patient’s natal Rasi and in '
                          'the Rasi governing the body part being operated '
                          'on, especially when afflicted by malefics.',
                          'Strengthen Mangala and the house governing the '
                          'body part; leave the 8th house unoccupied and '
                          'avoid mutual aspects between Mangala and Shani.',
                      ]},
    # — Panchaka-restricted activities —
    'cremation':         {'label': 'Cremation rites',
                          'audit_claim': 'muhurta.cremation.profile_conflict',
                          'skip_on_panchaka_nakshatra': True,
                          'manual_checks': [
                              'Known precision mismatch: Muhurta Chintamani '
                              'starts the cremation Panchaka restriction in '
                              'the latter half of Dhanishtha; this profile '
                              'currently rejects all of Dhanishtha.',
                              'Antyeshti is not a generic auspicious venture: '
                              'legal and medical requirements, timely rites, '
                              'family Sampradaya and the officiating priest’s '
                              'guidance override this project ranking.',
                          ]},
    'construction_roof': {'label': 'Roof-laying / construction milestone',
                          'source_claim': 'muhurta.construction_roof',
                          'skip_on_panchaka_nakshatra': True,
                          'allowed_lagnas': ['Vrishabha', 'Tula']},
    'wood_cutting':      {'label': 'Wood-cutting',
                          'source_claim': 'muhurta.wood_cutting',
                          'skip_on_panchaka_nakshatra': True,
                          'allowed_tithi_names': [
                              'Krishna Ashtami', 'Krishna Navami',
                              'Krishna Dashami', 'Krishna Ekadashi',
                              'Krishna Dwadashi', 'Krishna Trayodashi',
                              'Krishna Chaturdashi', 'Amavasya',
                          ],
                          'manual_checks': [
                              'Use a dry rising Rasi, preferably aspected '
                              'by a dry Graha; the finder does not classify '
                              'or evaluate this chart condition.',
                          ]},
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
                          'source_claim': 'muhurta.coronation',
                          'skip_on_yoga': list(_SAMSKARA_SKIP),
                          'prefer_nakshatra_mukha': (['Urdhva'], 1),
                          'allowed_nakshatras': [
                              'Ashwini', 'Rohini', 'Mrigashira',
                              'Punarvasu', 'Pushya', 'Uttara Phalguni',
                              'Hasta', 'Anuradha', 'Uttara Ashadha',
                              'Shravana', 'Uttara Bhadrapada', 'Revati',
                          ],
                          'allowed_tithi_names': [
                              'Shukla Pratipat', 'Shukla Dwitiya',
                              'Shukla Tritiya', 'Shukla Panchami',
                              'Shukla Saptami', 'Shukla Dashami',
                              'Shukla Ekadashi', 'Shukla Trayodashi',
                              'Pournami', 'Krishna Dwitiya',
                              'Krishna Dashami',
                          ],
                          'allowed_lagnas': [
                              'Mesha', 'Vrishabha', 'Mithuna', 'Karka',
                              'Simha', 'Dhanu', 'Kumbha', 'Meena',
                          ],
                          'manual_checks': [
                              'Strengthen Surya, Chandra, Lagna, the 10th '
                              'house and their lords; leave the 8th house '
                              'vacant and confine malefics to Upachayas.',
                              'For a traditional coronation, prefer Simha '
                              'Lagna occupied by Surya and aspected by Guru.',
                              'For a democratic government beginning, the '
                              'source instead describes Kumbha rising with '
                              'Shani in Kumbha or Tula, aspected by Guru or '
                              'Shukra.',
                          ]},
}

ACTIVITIES = tuple(ACTIVITY_RULES.keys())
