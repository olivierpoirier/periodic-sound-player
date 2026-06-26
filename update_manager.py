from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class UpdateResult:
    status: str
    version: str = ""
    release_url: str = ""
    download_url: str = ""
    error: str = ""


def check_for_update(repository: str, current_version: str, timeout: float = 5.0) -> UpdateResult:
    """Read the latest published GitHub release without blocking the UI thread."""
    api_url = f"https://api.github.com/repos/{repository}/releases/latest"
    request = Request(api_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "SoundMaker-Prank-Console"})

    try:
        with urlopen(request, timeout=timeout) as response:
            release = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            return UpdateResult(status="no_release", release_url=f"https://github.com/{repository}/releases")
        return UpdateResult(status="error", error=f"GitHub returned HTTP {exc.code}")
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return UpdateResult(status="error", error=str(exc))

    version = str(release.get("tag_name") or release.get("name") or "").strip()
    release_url = str(release.get("html_url") or f"https://github.com/{repository}/releases")
    assets = release.get("assets") or []
    download_url = _preferred_asset_url(assets)

    if not version:
        return UpdateResult(status="error", error="The latest release does not include a version tag.")
    if _is_newer(version, current_version):
        return UpdateResult(status="available", version=version, release_url=release_url, download_url=download_url)
    return UpdateResult(status="current", version=version, release_url=release_url)


def _preferred_asset_url(assets: list[object]) -> str:
    candidates = [asset for asset in assets if isinstance(asset, dict)]
    candidates.sort(key=lambda asset: _asset_priority(str(asset.get("name", ""))))
    if not candidates:
        return ""
    return str(candidates[0].get("browser_download_url", ""))


def _asset_priority(filename: str) -> int:
    lowered = filename.lower()
    if lowered.endswith(".exe"):
        return 0
    if lowered.endswith(".msi"):
        return 1
    if lowered.endswith(".zip"):
        return 2
    return 3


def _is_newer(candidate: str, current: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)*", value)
    if not match:
        return ()
    return tuple(int(part) for part in match.group(0).split("."))
