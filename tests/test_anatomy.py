import pytest

from pawnlink.api.anatomy import url_parts

URLS = [
    "https://github.com/login",
    "http://paypal-verify.xyz/login",
    "https://mu.qmmafe.com/",
    "https://www.tokopedia.com/search?q=laptop&page=2#top",
    "http://1.2.3.4/x.exe",
    "http://user:pw@shop.example.co.id:8080/a/b?c=d",
    "example.com/no-scheme",
    "http://[abc",
    "https://localhost/admin",
    "",
]


@pytest.mark.parametrize("url", URLS)
def test_parts_join_back_to_the_url(url):
    assert "".join(p["text"] for p in url_parts(url)) == url


def test_registered_domain_is_split():
    kinds = [(p["text"], p["kind"]) for p in url_parts("https://mu.qmmafe.com/")]
    assert kinds == [
        ("https://", "scheme"),
        ("mu.", "subdomain"),
        ("qmmafe", "domain"),
        (".com", "TLD"),
        ("/", "path"),
    ]


def test_multi_label_suffix_and_extras():
    kinds = {
        p["kind"]: p["text"] for p in url_parts("http://user:pw@shop.example.co.id:8080/a?b=1#c")
    }
    assert kinds["userinfo"] == "user:pw@"
    assert kinds["TLD"] == ".co.id"
    assert kinds["port"] == ":8080"
    assert kinds["query"] == "?b=1"
    assert kinds["fragment"] == "#c"


def test_ip_host_is_not_split():
    kinds = [p["kind"] for p in url_parts("http://1.2.3.4/x.exe")]
    assert kinds == ["scheme", "host", "path"]
