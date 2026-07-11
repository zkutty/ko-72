import hashlib
import hmac

from email_sender import _lang_from_tags, _unsubscribe_token, _unsubscribe_url


def test_lang_from_tags_none_defaults_to_en():
    assert _lang_from_tags(None) == "en"


def test_lang_from_tags_empty_list_defaults_to_en():
    assert _lang_from_tags([]) == "en"


def test_lang_from_tags_dict_shape():
    assert _lang_from_tags([{"name": "lang:ja"}]) == "ja"


def test_lang_from_tags_string_shape():
    assert _lang_from_tags(["lang:ja"]) == "ja"


def test_lang_from_tags_unknown_lang_defaults_to_en():
    assert _lang_from_tags(["lang:fr"]) == "en"


def test_lang_from_tags_ignores_unrelated_tags():
    assert _lang_from_tags(["vip", {"name": "beta-tester"}, "lang:ja"]) == "ja"


def test_lang_from_tags_case_and_whitespace_insensitive():
    assert _lang_from_tags(["lang: JA "]) == "ja"


def test_unsubscribe_token_is_deterministic(monkeypatch):
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "shared-secret")
    assert _unsubscribe_token("a@example.com") == _unsubscribe_token("A@Example.com  ")


def test_unsubscribe_token_matches_hmac_sha256(monkeypatch):
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "shared-secret")
    expected = hmac.new(b"shared-secret", b"a@example.com", hashlib.sha256).hexdigest()
    assert _unsubscribe_token("a@example.com") == expected


def test_unsubscribe_token_differs_per_email(monkeypatch):
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "shared-secret")
    assert _unsubscribe_token("a@example.com") != _unsubscribe_token("b@example.com")


def test_unsubscribe_url_embeds_email_and_token(monkeypatch):
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "shared-secret")
    url = _unsubscribe_url("a@example.com", "ja")
    assert url.startswith("https://ko-72.com/ja/unsubscribe.html?")
    assert "email=a%40example.com" in url
    assert f"token={_unsubscribe_token('a@example.com')}" in url
