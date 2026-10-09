import pytest

from pawnlink.features.extract import FEATURE_NAMES, extract_features


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


@pytest.mark.parametrize(
    ("url", "has_ext", "suspicious"),
    [
        ("http://evil.xyz/payload.EXE", 1, 1),
        ("http://1.2.3.4/bins/mirai.arm7", 1, 1),
        ("https://example.com/docs/index.html", 1, 0),
        ("https://example.com/", 0, 0),
        ("https://example.com/setup.exe?ref=mail", 1, 1),
    ],
)
def test_file_extension(url, has_ext, suspicious):
    f = extract_features(url)
    assert f["has_file_extension"] == has_ext
    assert f["has_suspicious_extension"] == suspicious


@pytest.mark.parametrize(
    "url",
    [
        "http://http://69.165.65.90/bins/x.sh",  # repeated scheme
        "http://[abc/x",  # urlsplit raises ValueError
        "http://",  # no host
        "http://intranet/login",  # dotless host
    ],
)
def test_malformed_urls_are_flagged_not_crashing(url):
    assert extract_features(url)["is_malformed"] == 1


@pytest.mark.parametrize(
    "url", ["https://example.com/", "http://116.53.34.145/i", "localhost:8000/x"]
)
def test_wellformed_urls_are_not_flagged(url):
    assert extract_features(url)["is_malformed"] == 0


def test_character_stats():
    f = extract_features("aab1%20")  # 3 alpha, 3 digits, 1 special, 6 unique
    assert f["pct_alpha"] == pytest.approx(3 / 7)
    assert f["num_special"] == 1
    assert f["num_percent_encoded"] == 1
    assert f["unique_char_ratio"] == pytest.approx(6 / 7)


def test_all_features_are_numeric():
    f = extract_features("https://www.example.com/a?b=c")
    assert all(isinstance(v, (int, float)) for v in f.values())


def test_feature_names_match_extract_output():
    assert list(extract_features("https://a.com/x")) == list(FEATURE_NAMES)


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
