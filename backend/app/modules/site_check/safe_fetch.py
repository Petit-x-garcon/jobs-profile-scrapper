"""SSRF-safe HTTP fetching for user-supplied URLs.

Every hop (including redirects) is resolved, checked to be a public address, and then
connected to by that exact IP, so DNS rebinding cannot swap in an internal address.
"""

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.shared.exceptions import BadRequest

MAX_REDIRECTS = 5
MAX_BODY_BYTES = 2 * 1024 * 1024
ALLOWED_PORTS = {None, 80, 443}  # None = scheme default


class FetchError(Exception):
    """The site could not be reached (DNS, connection, TLS, timeout, redirect loop)."""


@dataclass
class Fetched:
    """A fetched response, body capped at MAX_BODY_BYTES."""

    url: httpx.URL
    status: int
    content_type: str
    text: str


def parse_url(raw: str) -> httpx.URL:
    """Parse and validate a user URL; raise BadRequest if it is not a plain public web URL."""
    try:
        url = httpx.URL(raw.strip())
    except httpx.InvalidURL as exc:
        raise BadRequest("Enter a valid URL, e.g. https://example.com/jobs.") from exc
    if url.scheme not in ("http", "https") or not url.host:
        raise BadRequest("Enter a full http:// or https:// URL.")
    if url.userinfo:
        raise BadRequest("URLs containing credentials are not allowed.")
    if url.port not in ALLOWED_PORTS:
        raise BadRequest("Only the standard web ports (80 and 443) are allowed.")
    return url


def _is_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


async def _lookup(host: str) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return [str(info[4][0]).split("%")[0] for info in infos]  # drop IPv6 scope ids


async def resolve_public_ip(url: httpx.URL) -> str:
    """Resolve the host; raise BadRequest if any address is private/internal."""
    host = url.raw_host.decode("ascii")
    try:
        ips = [ipaddress.ip_address(ip) for ip in await _lookup(host)]
    except (socket.gaierror, UnicodeError) as exc:
        raise FetchError(f"Could not resolve the host name {host}.") from exc
    if not ips or not all(_is_public(ip) for ip in ips):
        raise BadRequest("This URL points to a private or internal address, which is blocked.")
    ipv4 = [ip for ip in ips if ip.version == 4]
    return str((ipv4 or ips)[0])


async def _read_text(response: httpx.Response) -> str:
    chunks: list[bytes] = []
    size = 0
    async for chunk in response.aiter_bytes():
        chunks.append(chunk)
        size += len(chunk)
        if size >= MAX_BODY_BYTES:
            break
    body = b"".join(chunks)[:MAX_BODY_BYTES]
    try:
        return body.decode(response.encoding or "utf-8", errors="replace")
    except LookupError:  # unknown charset name in the header
        return body.decode("utf-8", errors="replace")


async def _send_pinned(client: httpx.AsyncClient, method: str, url: httpx.URL) -> httpx.Response:
    ip = await resolve_public_ip(url)
    request = client.build_request(
        method,
        url.copy_with(host=ip),
        headers={"Host": url.netloc.decode("ascii")},
        extensions={"sni_hostname": url.raw_host.decode("ascii")},  # TLS still verifies the name
    )
    return await client.send(request, stream=True)


async def fetch(
    client: httpx.AsyncClient,
    url: httpx.URL,
    method: str = "GET",
    *,
    check_redirect: Callable[[httpx.URL], Awaitable[None]] | None = None,
) -> Fetched:
    """Fetch `url`, following up to MAX_REDIRECTS redirects, each validated like the first.

    Raises BadRequest for unsafe targets and FetchError when the site cannot be reached.
    The client must have follow_redirects=False.
    """
    for _ in range(MAX_REDIRECTS + 1):
        try:
            response = await _send_pinned(client, method, url)
        except httpx.HTTPError as exc:
            raise FetchError(f"Could not connect ({type(exc).__name__}).") from exc
        try:
            if response.is_redirect:
                url = parse_url(str(url.join(response.headers["location"])))
                if check_redirect is not None:
                    await check_redirect(url)
                continue
            text = await _read_text(response) if method == "GET" else ""
            content_type = response.headers.get("content-type", "")
            return Fetched(url, response.status_code, content_type, text)
        except httpx.HTTPError as exc:
            raise FetchError(f"The connection failed ({type(exc).__name__}).") from exc
        finally:
            await response.aclose()
    raise FetchError("Too many redirects.")
