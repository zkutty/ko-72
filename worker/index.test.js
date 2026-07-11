import { test } from "node:test";
import assert from "node:assert/strict";

import seasonsData from "../data/seasons.json" with { type: "json" };
import {
  findActiveSeason,
  getSeasonDateRangeForLang,
  compareMonthDay,
  unsubscribeToken,
  timingSafeEqual,
} from "./index.js";

const seasons = seasonsData.seasons;

test("all 72 seasons are present", () => {
  assert.equal(seasons.length, 72);
});

test("compareMonthDay orders chronologically within a year", () => {
  const jan5 = { start_month: 1, start_day: 5 };
  const jan10 = { start_month: 1, start_day: 10 };
  const dec27 = { start_month: 12, start_day: 27 };
  assert.ok(compareMonthDay(jan5, jan10) < 0);
  assert.ok(compareMonthDay(jan10, jan5) > 0);
  assert.ok(compareMonthDay(dec27, jan5) > 0);
  assert.equal(compareMonthDay(jan5, jan5), 0);
});

test("findActiveSeason on an exact start date", () => {
  const today = new Date(Date.UTC(2026, 0, 5)); // Jan 5
  assert.equal(findActiveSeason(today).id, 1);
});

test("findActiveSeason mid-season", () => {
  const today = new Date(Date.UTC(2026, 0, 12)); // Jan 12, season #2 starts Jan 10
  assert.equal(findActiveSeason(today).id, 2);
});

test("findActiveSeason falls back to the previous year on Jan 1", () => {
  // Season #1 starts Jan 5 — Jan 1 is before that, so the active season must
  // come from the previous-year fallback: season #72 (starts Jan 1).
  const today = new Date(Date.UTC(2026, 0, 1));
  assert.equal(findActiveSeason(today).id, 72);
});

test("findActiveSeason late December", () => {
  const today = new Date(Date.UTC(2026, 11, 29)); // Dec 29, season #71 starts Dec 27
  assert.equal(findActiveSeason(today).id, 71);
});

test("getSeasonDateRangeForLang: all 72 seasons produce a positive duration", () => {
  for (const season of seasons) {
    const { duration } = getSeasonDateRangeForLang(season, "en");
    assert.ok(duration >= 1, `season #${season.id} has non-positive duration (${duration})`);
  }
});

test("getSeasonDateRangeForLang: season 71 -> 72 year-boundary wrap", () => {
  const s71 = seasons.find((s) => s.id === 71);
  const s72 = seasons.find((s) => s.id === 72);

  const r71 = getSeasonDateRangeForLang(s71, "en");
  assert.equal(r71.duration, 5);

  const r72 = getSeasonDateRangeForLang(s72, "en");
  assert.equal(r72.duration, 4);
});

test("getSeasonDateRangeForLang: Japanese date format", () => {
  const s1 = seasons.find((s) => s.id === 1);
  const { dateRange } = getSeasonDateRangeForLang(s1, "ja");
  assert.match(dateRange, /月.*日.*–.*月.*日/);
});

test("unsubscribeToken is deterministic for the same secret + email", async () => {
  const a = await unsubscribeToken("shared-secret", "a@example.com");
  const b = await unsubscribeToken("shared-secret", "a@example.com");
  assert.equal(a, b);
});

test("unsubscribeToken differs across emails and secrets", async () => {
  const a = await unsubscribeToken("shared-secret", "a@example.com");
  const b = await unsubscribeToken("shared-secret", "b@example.com");
  const c = await unsubscribeToken("other-secret", "a@example.com");
  assert.notEqual(a, b);
  assert.notEqual(a, c);
});

test("timingSafeEqual", () => {
  assert.equal(timingSafeEqual("abc123", "abc123"), true);
  assert.equal(timingSafeEqual("abc123", "abc124"), false);
  assert.equal(timingSafeEqual("abc123", "abc12"), false);
  assert.equal(timingSafeEqual("abc123", undefined), false);
});
