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
    # Somavaram (Monday) + Tritiya (Jaya) + Chitra: Chitra is not in Monday's
    # Sarvartha/Amrita tables, tithi 3 is not Monday's Visha/Dagdha, and
    # Jaya's Siddha Yoga partner is Tuesday not Monday.
    result = get_special_yogas('Somavaram', 'Shukla Tritiya', 'Chitra')
    assert result == []


def test_dvipushkara_yoga_match():
    # Adivaram + Shukla Dwitiya (tithi 2) + Mrigashira
    result = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Mrigashira')
    assert 'Dvipushkara Yoga' in result


def test_dvipushkara_yoga_no_match_wrong_vara():
    result = get_special_yogas('Somavaram', 'Shukla Dwitiya', 'Mrigashira')
    assert 'Dvipushkara Yoga' not in result


def test_dvipushkara_yoga_no_match_wrong_nakshatra():
    result = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Rohini')
    assert 'Dvipushkara Yoga' not in result


def test_tripushkara_yoga_match():
    # Mangalavaram + Shukla Dwitiya (tithi 2) + Krittika
    result = get_special_yogas('Mangalavaram', 'Shukla Dwitiya', 'Krittika')
    assert 'Tripushkara Yoga' in result


def test_tripushkara_yoga_no_match_wrong_vara():
    result = get_special_yogas('Guruvaram', 'Shukla Dwitiya', 'Krittika')
    assert 'Tripushkara Yoga' not in result


def test_tripushkara_yoga_no_match_wrong_tithi():
    # Tritiya (tithi 3) is NOT a Tripushkara tithi
    result = get_special_yogas('Mangalavaram', 'Shukla Tritiya', 'Krittika')
    assert 'Tripushkara Yoga' not in result


def test_siddha_yoga_nanda_friday():
    result = get_special_yogas('Shukravaram', 'Shukla Pratipat', 'Chitra')
    assert 'Siddha Yoga' in result


def test_siddha_yoga_bhadra_wednesday():
    result = get_special_yogas('Budhavaram', 'Shukla Dwitiya', 'Hasta')
    assert 'Siddha Yoga' in result


def test_siddha_yoga_jaya_tuesday():
    result = get_special_yogas('Mangalavaram', 'Shukla Tritiya', 'Chitra')
    assert 'Siddha Yoga' in result


def test_siddha_yoga_purna_thursday():
    result = get_special_yogas('Guruvaram', 'Shukla Panchami', 'Hasta')
    assert 'Siddha Yoga' in result


def test_siddha_yoga_purna_pournami_thursday():
    # Pournami is also Purna family — Siddha Yoga still fires.
    result = get_special_yogas('Guruvaram', 'Pournami', 'Hasta')
    assert 'Siddha Yoga' in result


def test_siddha_yoga_rikta_no_match():
    # Rikta has no Siddha Yoga partner on any weekday.
    for vara in ('Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
                 'Guruvaram', 'Shukravaram', 'Shanivaram'):
        result = get_special_yogas(vara, 'Shukla Chaturthi', 'Chitra')
        assert 'Siddha Yoga' not in result, f'unexpected Siddha Yoga on {vara} + Rikta'


def test_siddha_yoga_wrong_vara_no_match():
    # Nanda tithi on Thursday should NOT give Siddha Yoga (needs Friday).
    result = get_special_yogas('Guruvaram', 'Shukla Pratipat', 'Chitra')
    assert 'Siddha Yoga' not in result


def test_dvipushkara_and_tripushkara_not_both_on_same_day():
    # Both yogas share tithis {2,7,12} on Pushkara varas,
    # mutual exclusivity comes from disjoint nakshatra sets.
    dvi = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Mrigashira')
    tri = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Krittika')
    assert 'Dvipushkara Yoga' in dvi
    assert 'Tripushkara Yoga' not in dvi
    assert 'Tripushkara Yoga' in tri
    assert 'Dvipushkara Yoga' not in tri
