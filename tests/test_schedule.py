from datetime import date, datetime, timezone

from price_checker import schedule


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_due_after_8am_uk_once_per_day():
    # 8 Nov is GMT, so 07:59 UTC is 07:59 in the UK.
    assert schedule.is_due(utc(2026, 11, 8, 7, 59), None)[0] is False
    assert schedule.is_due(utc(2026, 11, 8, 8, 0), None)[0] is True
    # A run that GitHub started six hours late still posts...
    assert schedule.is_due(utc(2026, 11, 8, 14, 53), date(2026, 11, 7))[0] is True
    # ...but only once.
    assert schedule.is_due(utc(2026, 11, 8, 15, 30), date(2026, 11, 8))[0] is False


def test_due_follows_british_summer_time():
    # 1 Jul is BST (UTC+1): 07:10 UTC is already 08:10 in the UK.
    assert schedule.is_due(utc(2026, 7, 1, 7, 10), None)[0] is True
    assert schedule.is_due(utc(2026, 7, 1, 6, 50), None)[0] is False


def test_record_and_read_last_posted(tmp_path):
    path = tmp_path / "digest_state.json"
    assert schedule.last_posted(path) is None
    # 23:30 UTC on 30 Jun is already 1 Jul in the UK.
    schedule.record_posted(path, utc(2026, 6, 30, 23, 30))
    assert schedule.last_posted(path) == date(2026, 7, 1)
    path.write_text("not json")
    assert schedule.last_posted(path) is None
