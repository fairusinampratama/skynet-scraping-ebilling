from sync import parse_date, parse_period_to_date
import datetime

def test_parse_date():
    # Test happy path
    parsed = parse_date("03-October-2022")
    assert parsed == datetime.date(2022, 10, 3)
    
    # Test valid but edge casing
    parsed2 = parse_date("28-February-2024")
    assert parsed2 == datetime.date(2024, 2, 28)

def test_parse_date_invalid():
    # Test missing payload fallback
    assert parse_date("-") is None
    assert parse_date("") is None
    assert parse_date(None) is None
    
    # Test garbage string fallback
    assert parse_date("invalid-date-format") is None

def test_parse_period_to_date():
    # Test Indonesian Mapping
    d1 = parse_period_to_date("Maret 2026")
    assert d1 == datetime.date(2026, 3, 1)

    d2 = parse_period_to_date("Desember 2025")
    assert d2 == datetime.date(2025, 12, 1)
    
    # Test English mapping interchangeably
    d3 = parse_period_to_date("March 2026")
    assert d3 == datetime.date(2026, 3, 1)

def test_parse_period_to_date_invalid():
    assert parse_period_to_date(None) is None
    assert parse_period_to_date("BulanDepan 2026") is None
