from telugu_panchangam.special_yogas import get_special_yogas


def test_sarvartha_siddhi_match():
    # Mangalavaram + Krittika is in the Sarvartha Siddhi table for Tuesday.
    # Tithi number 1 (Pratipat) doesn't trigger Visha or Dagdha on any weekday.
    result = get_special_yogas('Mangalavaram', 'Shukla Pratipat', 'Krittika')
    assert result == ['Sarvartha Siddhi Yoga']


def test_amrita_siddhi_match():
    # Shanivaram + Rohini triggers both Sarvartha Siddhi and Amrita Siddhi for Saturday.
    result = get_special_yogas('Shanivaram', 'Shukla Pratipat', 'Rohini')
    assert 'Amrita Siddhi Yoga' in result
    assert 'Sarvartha Siddhi Yoga' in result


def test_visha_yoga_match():
    # Budhavaram (Wednesday) + Ashtami (tithi number 8) triggers Visha Yoga.
    # Chitra is not in Wednesday's Sarvartha/Amrita tables, and 8 is not a
    # Wednesday Dagdha tithi (those are 2 and 3).
    result = get_special_yogas('Budhavaram', 'Shukla Ashtami', 'Chitra')
    assert result == ['Visha Yoga']


def test_dagdha_yoga_match():
    # Guruvaram (Thursday) Dagdha tithi is 6. Krishna Shashthi is tithi number 6
    # ((TITHI_NAMES index 20 % 15) + 1 == 6).
    result = get_special_yogas('Guruvaram', 'Krishna Shashthi', 'Chitra')
    assert result == ['Dagdha Yoga']


def test_dagdha_yoga_wednesday_two_tithis():
    # Wednesday has two Dagdha tithis: 2 and 3. Tritiya is tithi number 3.
    result = get_special_yogas('Budhavaram', 'Shukla Tritiya', 'Chitra')
    assert result == ['Dagdha Yoga']


def test_multiple_yogas_same_day():
    # Adivaram (Sunday) + Hasta is both Sarvartha Siddhi and Amrita Siddhi for Sunday.
    # Tithi number 5 (Panchami) is also Sunday's Visha Yoga tithi.
    result = get_special_yogas('Adivaram', 'Shukla Panchami', 'Hasta')
    assert result == ['Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga', 'Visha Yoga']


def test_no_yoga():
    # Mangalavaram + Chitra + tithi number 3 matches none of the four tables.
    result = get_special_yogas('Mangalavaram', 'Shukla Tritiya', 'Chitra')
    assert result == []
