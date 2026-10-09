import pytest

from pawnlink.features.extract import extract_features


def test_basic_url():
    f = extract_features("https://www.example.com/login?user=a&next=b")
    assert f["url_length"] == 43
    assert f["num_dots"] == 2
    assert f["has_https"] == 1
    assert f["host_length"] == len("www.example.com")
    assert f["path_length"] == len("/login")
    assert f["num_query_params"] == 2


def test_url_without_scheme_still_has_host():
    f = extract_features("example.com/login")
    assert f["host_length"] == len("example.com")
    assert f["has_https"] == 0


def test_ip_url_with_port():
    # In the raw dataset this URL has tld_length = 9, which is wrong.
    f = extract_features("http://116.53.34.145:34075/i")
    assert f["has_ip"] == 1
    assert f["host_length"] == len("116.53.34.145")


def test_multi_part_tld():
    f = extract_features("https://login.secure.paypal.co.uk/")
    assert f["tld_length"] == len("co.uk")
    assert f["domain_length"] == len("paypal")
    assert f["subdomain_count"] == 2
    assert f["is_popular_tld"] == 0


def test_ip_url_has_no_tld():
    f = extract_features("http://116.53.34.145:34075/i")
    assert f["tld_length"] == 0
    assert f["subdomain_count"] == 0


def test_empty_url_does_not_crash():
    f = extract_features("")
    assert f["url_length"] == 0
    assert f["pct_digits"] == 0.0
    assert f["url_entropy"] == 0.0


def test_entropy_of_repeated_char_is_zero():
    assert extract_features("aaaa")["url_entropy"] == pytest.approx(0.0)


def test_same_url_gives_same_features():
    url = "http://login.paypal.com.evil.xyz/verify"
    assert extract_features(url) == extract_features(url)
