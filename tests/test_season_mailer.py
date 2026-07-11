from datetime import date

import pytest

from season_mailer import (
    enrich_seasons_with_end_dates,
    find_active_season,
    find_todays_season,
    load_seasons,
    season_occurrence_year,
)


@pytest.fixture(scope="module")
def raw_seasons():
    return load_seasons()


@pytest.fixture(scope="module")
def enriched(raw_seasons):
    return enrich_seasons_with_end_dates(raw_seasons, year=2026)


def test_all_72_seasons_present(raw_seasons):
    assert len(raw_seasons) == 72
    assert {s["id"] for s in raw_seasons} == set(range(1, 73))


def test_all_seasons_have_positive_duration(enriched):
    for s in enriched:
        assert s["duration_days"] >= 1, f"season #{s['id']} has non-positive duration"


def test_year_boundary_wrap_seasons_71_and_72(enriched):
    """Season 71 (Dec 27) precedes season 72 (Jan 1) chronologically even
    though season 72's month/day is numerically smaller — this is the exact
    case that used to produce a negative duration for #71 and a ~369-day
    duration for #72."""
    by_id = {s["id"]: s for s in enriched}

    s71 = by_id[71]
    assert (s71["start_month"], s71["start_day"]) == (12, 27)
    assert (s71["end_month"], s71["end_day"]) == (12, 31)
    assert s71["duration_days"] == 5

    s72 = by_id[72]
    assert (s72["start_month"], s72["start_day"]) == (1, 1)
    assert (s72["end_month"], s72["end_day"]) == (1, 4)
    assert s72["duration_days"] == 4


def test_seasons_are_contiguous(enriched):
    """Each season's end date is exactly one day before the next season's
    start date (in list order, wrapping from #72 back to #1). Uses a fixed
    reference year for the (month, day) arithmetic only — the year itself
    doesn't matter here, just that there's no gap or overlap."""
    from datetime import timedelta

    for i, s in enumerate(enriched):
        nxt = enriched[(i + 1) % len(enriched)]
        end = date(2001, s["end_month"], s["end_day"])  # non-leap year, matches the 2026 fixture
        day_after_end = end + timedelta(days=1)
        assert (day_after_end.month, day_after_end.day) == (nxt["start_month"], nxt["start_day"])


def test_find_todays_season_matches_exact_start_date(raw_seasons):
    season = find_todays_season(raw_seasons, date(2026, 1, 5))
    assert season is not None
    assert season["id"] == 1


def test_find_todays_season_returns_none_mid_season(raw_seasons):
    assert find_todays_season(raw_seasons, date(2026, 1, 7)) is None


def test_find_active_season_on_exact_start_date(raw_seasons):
    assert find_active_season(raw_seasons, date(2026, 1, 5))["id"] == 1


def test_find_active_season_mid_season(raw_seasons):
    # Season 2 starts Jan 10 — Jan 12 is mid-way through it.
    assert find_active_season(raw_seasons, date(2026, 1, 12))["id"] == 2


def test_find_active_season_jan_1_fallback_to_previous_year(raw_seasons):
    """Jan 1 falls before season #1's Jan 5 start in the current year, so the
    active season must be found via the previous-year fallback: the
    last season to start (chronologically) is #72, which starts Jan 1."""
    assert find_active_season(raw_seasons, date(2026, 1, 1))["id"] == 72
    assert find_active_season(raw_seasons, date(2026, 1, 4))["id"] == 72
    assert find_active_season(raw_seasons, date(2026, 1, 3))["id"] == 72


def test_find_active_season_late_december(raw_seasons):
    assert find_active_season(raw_seasons, date(2026, 12, 29))["id"] == 71


def test_season_occurrence_year_same_year(raw_seasons):
    season1 = next(s for s in raw_seasons if s["id"] == 1)  # Jan 5
    assert season_occurrence_year(season1, date(2026, 1, 5)) == 2026
    assert season_occurrence_year(season1, date(2026, 1, 9)) == 2026


def test_season_occurrence_year_wraps_to_previous_year(raw_seasons):
    """A season that starts in late December is still 'this occurrence' when
    today has already rolled into January of the following year."""
    season71 = next(s for s in raw_seasons if s["id"] == 71)  # Dec 27
    assert season_occurrence_year(season71, date(2027, 1, 2)) == 2026
