"""Calendar vocabulary constants — names of Tithis, Nakshatras, Raashis, etc.

Kept as a standalone, import-free module so that both the engine layer
(engines/base.py) and the yoga/muhurta layer (special_yogas.py, panchaka.py,
etc.) can import these constants without creating a circular dependency.
"""

TITHI_NAMES: list[str] = [
    # Shukla Paksha (0-14)
    'Shukla Pratipat', 'Shukla Dwitiya', 'Shukla Tritiya', 'Shukla Chaturthi',
    'Shukla Panchami', 'Shukla Shashthi', 'Shukla Saptami', 'Shukla Ashtami',
    'Shukla Navami', 'Shukla Dashami', 'Shukla Ekadashi', 'Shukla Dwadashi',
    'Shukla Trayodashi', 'Shukla Chaturdashi', 'Pournami',
    # Krishna Paksha (15-29)
    'Krishna Pratipat', 'Krishna Dwitiya', 'Krishna Tritiya', 'Krishna Chaturthi',
    'Krishna Panchami', 'Krishna Shashthi', 'Krishna Saptami', 'Krishna Ashtami',
    'Krishna Navami', 'Krishna Dashami', 'Krishna Ekadashi', 'Krishna Dwadashi',
    'Krishna Trayodashi', 'Krishna Chaturdashi', 'Amavasya',
]

NAKSHATRA_NAMES: list[str] = [
    'Ashvini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha',
    'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha',
    'Shravana', 'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
    'Uttara Bhadrapada', 'Revati',
]

YOGA_NAMES: list[str] = [
    'Vishkambha', 'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda',
    'Sukarma', 'Dhriti', 'Shoola', 'Ganda', 'Vriddhi', 'Dhruva',
    'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyan',
    'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla',
    'Brahma', 'Indra', 'Vaidhriti',
]

RASHI_NAMES: list[str] = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
    'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
]

MAASAM_NAMES: list[str] = [
    'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha',
    'Shravana', 'Bhadrapada', 'Ashvina', 'Kartika',
    'Margashira', 'Pushya', 'Magha', 'Phalguna',
]

SAMVATSARA_NAMES: list[str] = [
    'Prabhava', 'Vibhava', 'Shukla', 'Pramoduta', 'Prajapati',
    'Angirasa', 'Shrimukha', 'Bhava', 'Yuva', 'Dhata',
    'Ishvara', 'Bahudhanya', 'Pramadi', 'Vikrama', 'Vrisha',
    'Chitrabhanu', 'Subhanu', 'Tarana', 'Parthiva', 'Vyaya',
    'Sarvajit', 'Sarvadharin', 'Virodhi', 'Vikrita', 'Khara',
    'Nandana', 'Vijaya', 'Jaya', 'Manmatha', 'Durmukhi',
    'Hevilambi', 'Vilambi', 'Vikari', 'Sharvari', 'Plava',
    'Shubhakrit', 'Shobhakrit', 'Krodhi', 'Vishvavasu', 'Parabhava',
    'Plavanga', 'Kilaka', 'Saumya', 'Sadharana', 'Virodhikrit',
    'Paridhavi', 'Pramadicha', 'Ananda', 'Rakshasa', 'Nala',
    'Pingala', 'Kalayukti', 'Siddharthi', 'Raudra', 'Durmati',
    'Dundubhi', 'Rudhirodgari', 'Raktakshi', 'Krodhana', 'Kshaya',
]

# Drik ritu: seasons are tropical (sayana), anchored to the solstices —
# Shishira starts at Uttarayana (winter solstice), each ritu spans two
# tropical signs. Indexed by tropical sun sign (0 = Aries .. 11 = Pisces).
# Verified against drikpanchang.com "Drik Ritu" (e.g. Grishma 2026 runs
# Apr 20 - Jun 21, the tropical Taurus + Gemini stretch).
RITUVU_NAMES: list[str] = [
    'Vasanta',                 # Aries
    'Grishma', 'Grishma',      # Taurus, Gemini
    'Varsha', 'Varsha',        # Cancer, Leo
    'Sharad', 'Sharad',        # Virgo, Libra
    'Hemanta', 'Hemanta',      # Scorpio, Sagittarius
    'Shishira', 'Shishira',    # Capricorn, Aquarius
    'Vasanta',                 # Pisces
]

VAARAM_NAMES: list[str] = [
    'Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
    'Guruvaram', 'Shukravaram', 'Shanivaram',
]

KARANA_REPEATING: list[str] = [
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Garaja', 'Vanija', 'Vishti',
]
KARANA_FIXED: dict[int, str] = {
    0: 'Kinstughna',
    57: 'Shakuni',
    58: 'Chatushpada',
    59: 'Naga',
}

# Traditional Ekadashi names by Amanta maasam and paksham. Both Ekadashis of
# an Adhika maasam have their own names (Padmini/Parama) regardless of month.
EKADASHI_NAMES: dict[str, dict[str, str]] = {
    'Chaitra':    {'Shukla': 'Kamada',      'Krishna': 'Varuthini'},
    'Vaishakha':  {'Shukla': 'Mohini',      'Krishna': 'Apara'},
    'Jyeshtha':   {'Shukla': 'Nirjala',     'Krishna': 'Yogini'},
    'Ashadha':    {'Shukla': 'Shayani',     'Krishna': 'Kamika'},
    'Shravana':   {'Shukla': 'Putrada',     'Krishna': 'Aja'},
    'Bhadrapada': {'Shukla': 'Parivartini', 'Krishna': 'Indira'},
    'Ashvina':    {'Shukla': 'Papankusha',  'Krishna': 'Rama'},
    'Kartika':    {'Shukla': 'Prabodhini',  'Krishna': 'Utpanna'},
    'Margashira': {'Shukla': 'Mokshada',    'Krishna': 'Saphala'},
    'Pushya':     {'Shukla': 'Putrada',     'Krishna': 'Shattila'},
    'Magha':      {'Shukla': 'Jaya',        'Krishna': 'Vijaya'},
    'Phalguna':   {'Shukla': 'Amalaki',     'Krishna': 'Papamochani'},
}

GANDA_MOOLA_NAKSHATRAS: frozenset[str] = frozenset(
    {'Ashvini', 'Ashlesha', 'Magha', 'Jyeshtha', 'Mula', 'Revati'})
