import pytest
import truststore

from karakeep_mcp.config import load_settings, ssl_context

BASE = {"KARAKEEP_URL": "https://karakeep.example"}


def test_missing_karakeep_url_names_the_variable():
    with pytest.raises(RuntimeError, match="KARAKEEP_URL"):
        load_settings({})


def test_public_url_defaults_to_karakeep_url():
    assert load_settings(BASE).public_url == "https://karakeep.example"


def test_public_url_can_differ():
    s = load_settings({"KARAKEEP_URL": "http://10.0.0.5:3000", "KARAKEEP_PUBLIC_URL": "https://karakeep.example/"})
    assert (s.karakeep_url, s.public_url) == ("http://10.0.0.5:3000", "https://karakeep.example")


def test_trailing_slash_is_stripped():
    assert load_settings({"KARAKEEP_URL": "https://karakeep.example/"}).karakeep_url == "https://karakeep.example"


def test_defaults():
    s = load_settings(BASE)
    assert (s.host, s.port, s.verify_tls, s.allowed_hosts, s.base_url, s.oauth_secret) == ("0.0.0.0", 8000, True, [], None, None)
    assert str(s.data_dir) == "/data"


def test_ssl_context_is_truststore():
    assert isinstance(ssl_context(load_settings(BASE)), truststore.SSLContext)


def test_verify_tls_false_turns_checking_off():
    assert ssl_context(load_settings({**BASE, "VERIFY_TLS": "false"})) is False
