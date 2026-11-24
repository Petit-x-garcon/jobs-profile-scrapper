"""Site check tests: DNS is faked and HTTP is mocked with respx, no network."""

import socket
from unittest.mock import patch

import httpx
import pytest
import respx

from app.modules.site_check import safe_fetch

IP = "93.184.216.34"
BASE = f"https://{IP}"
ARTICLE = (
    "<html><body><script>var x=1</script><p>" + "Senior Python job. " * 30 + "</p></body></html>"
)


@pytest.fixture
def dns():
    """Map host -> IPs; unknown hosts fail to resolve."""
    table: dict[str, list[str]] = {"example.com": [IP]}

    async def lookup(host: str) -> list[str]:
        if host not in table:
            raise socket.gaierror("nope")
        return table[host]

    with patch.object(safe_fetch, "_lookup", lookup):
        yield table


async def _check(client, url: str) -> httpx.Response:
    return await client.post("/api/site-check", json={"url": url})


@pytest.mark.parametrize(
    "url",
    ["ftp://example.com", "https://user:pw@example.com", "https://example.com:8080/", "nonsense"],
)
async def test_rejects_invalid_urls(client, dns, url):
    r = await _check(client, url)
    assert r.status_code == 400
    assert isinstance(r.json()["detail"], str)


@pytest.mark.parametrize(
    "ip", ["127.0.0.1", "10.0.0.5", "169.254.169.254", "::1", "::ffff:127.0.0.1", "100.64.0.1"]
)
@respx.mock(assert_all_called=False)
async def test_blocks_private_addresses(client, dns, ip):
    dns["internal.test"] = [IP, ip]  # one bad address is enough to block
    r = await _check(client, "https://internal.test/")
    assert r.status_code == 400
    assert "private or internal" in r.json()["detail"]
    assert not respx.calls  # nothing was requested


@respx.mock
async def test_successful_extraction_pins_ip(client, dns):
    respx.get(f"{BASE}/robots.txt").respond(200, text="User-agent: *\nDisallow: /admin\n")
    page = respx.get(f"{BASE}/jobs").respond(200, html=ARTICLE)
    body = (await _check(client, "https://example.com/jobs")).json()
    assert (body["result"], body["http_status"], body["robots_status"]) == (
        "successful",
        200,
        "allowed",
    )
    assert body["content_preview"].startswith("Senior Python job.")
    assert "var x" not in body["content_preview"]
    assert "does not guarantee permission" in body["message"]
    assert page.calls.last.request.headers["host"] == "example.com"


@respx.mock
async def test_robots_disallow_is_restricted_and_skips_content(client, dns):
    respx.get(f"{BASE}/robots.txt").respond(200, text="User-agent: *\nDisallow: /\n")
    head = respx.head(f"{BASE}/jobs").respond(200)
    get = respx.get(f"{BASE}/jobs").respond(200, html=ARTICLE)
    body = (await _check(client, "https://example.com/jobs")).json()
    assert (body["result"], body["robots_status"], body["http_status"]) == (
        "restricted",
        "disallowed",
        200,
    )
    assert body["content_preview"] is None
    assert head.called and not get.called


@respx.mock
async def test_redirect_to_internal_host_is_blocked(client, dns):
    dns["evil.test"] = ["192.168.1.1"]
    respx.get(f"{BASE}/robots.txt").respond(404)
    respx.get(f"{BASE}/go").respond(302, headers={"Location": "http://evil.test/admin"})
    r = await _check(client, "https://example.com/go")
    assert r.status_code == 400


@respx.mock
async def test_blocked_and_js_pages(client, dns):
    respx.get(f"{BASE}/robots.txt").respond(404)
    respx.get(f"{BASE}/login").respond(403, html="Forbidden")
    respx.get(f"{BASE}/spa").respond(200, html="<div id=root></div><script>app()</script>")
    login = (await _check(client, "https://example.com/login")).json()
    assert (login["result"], login["robots_status"]) == ("restricted", "not_found")
    spa = (await _check(client, "https://example.com/spa")).json()
    assert spa["result"] == "inconclusive"


async def test_unresolvable_host_fails(client, dns):
    body = (await _check(client, "https://no-such-host.test/")).json()
    assert body["result"] == "failed"
    assert "resolve" in body["message"]


@respx.mock
async def test_save_and_scrape_successful_url(client, db, dns):
    from app.modules.site_check.service import list_source_urls, scrape_source

    url = "https://example.com/jobs/1"
    respx.get(f"{BASE}/robots.txt").respond(200, text="User-agent: *\nDisallow: /admin")
    respx.get(f"{BASE}/jobs/1").respond(
        200,
        html=ARTICLE.replace(
            "</body>",
            """
        <script type="application/ld+json">
        {"@graph":[{"@type":"JobPosting","title":"Python Developer",
        "hiringOrganization":{"name":"Example Inc"},
        "description":"<p>Build software.</p><p>Maintain tests.</p>"}]}
        </script></body>
        """,
        ),
    )

    first = await client.post("/api/site-check/sources", json={"url": url})
    second = await client.post("/api/site-check/sources", json={"url": url + "#overview"})
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert await list_source_urls(db) == [url]

    job = await scrape_source(url)
    assert job is not None
    assert (job.title, job.company, job.source, job.url) == (
        "Python Developer",
        "Example Inc",
        "website",
        url,
    )
    assert job.description == "Build software.\nMaintain tests."

    respx.get(f"{BASE}/robots.txt").respond(200, text="User-agent: *\nDisallow: /jobs")
    respx.head(f"{BASE}/jobs/1").respond(200)
    assert await scrape_source(url) is None


@respx.mock
async def test_source_rejects_redirect_to_disallowed_page(client, db, dns):
    from app.modules.site_check.service import list_source_urls

    respx.get(f"{BASE}/robots.txt").respond(200, text="User-agent: *\nDisallow: /blocked")
    respx.get(f"{BASE}/go").respond(302, headers={"Location": "/blocked"})
    blocked = respx.get(f"{BASE}/blocked").respond(200, html=ARTICLE)

    response = await client.post("/api/site-check/sources", json={"url": "https://example.com/go"})
    assert response.status_code == 400
    assert not blocked.called
    assert await list_source_urls(db) == []
