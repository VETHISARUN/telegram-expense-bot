# tests/test_parser.py
import datetime
from mybot.utils import parse_expense

def test_parse_expense_valid():
    date, desc, amount = parse_expense("01/06/2025, Train, 80")
    assert desc == "Train"
    assert amount == 80
    assert isinstance(date, datetime.date)

def test_parse_expense_invalid():
    result = parse_expense("invalid text")
    assert result is None
