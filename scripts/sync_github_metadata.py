#!/usr/bin/env python3
"""
Sync GitHub repository metadata (description, topics, and release notes)
for Glyph - Text Extractor using the GitHub REST API.
"""

import argparse
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO_DEFAULT = "muhaideennausar/glyph-text-extractor"
TARGET_DESCRIPTION = "Screen text extractor and OCR utility for Linux desktops (Wayland and X11)"
TARGET_HOMEPAGE = "https://github.com/muhaideennausar/glyph-text-extractor"
TARGET_TOPICS = [
    "ocr",
    "screen-capture",
    "wayland",
    "gtk4",
    "libadwaita",
    "tesseract-ocr",
    "linux-desktop",
    "text-extractor",
]


def load_release_notes(file_path="docs/GITHUB_RELEASES.md"):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Release notes file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = re.split(r"\n## (v[0-9]+\.[0-9]+\.[0-9]+[^\n]*)\n", content)
    releases = {}
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        tag = header.split()[0]
        body = sections[i + 1].strip()
        if body.endswith("---"):
            body = body[:-3].strip()
        releases[tag] = f"## Glyph - Text Extractor {tag}\n\n" + body
    return releases


def github_api_request(url, method="GET", data=None, token=""):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Glyph-Metadata-Sync",
    }
    payload = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            message = err_json.get("message", err_msg)
        except Exception:
            message = err_msg
        raise RuntimeError(f"HTTP {e.code} on {method} {url}: {message}")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize GitHub repository description, topics, and release notes."
    )
    parser.add_argument(
        "--repo",
        default=REPO_DEFAULT,
        help=f"Target GitHub repository (default: {REPO_DEFAULT})",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="GitHub Personal Access Token with repo scope (or set GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without sending update requests",
    )
    args = parser.parse_args()

    token = (
        args.token
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
    )
    if not token and not args.dry_run:
        print("A GitHub Personal Access Token (PAT) with 'repo' scope is required.")
        token = getpass.getpass("Enter GitHub Personal Access Token: ").strip()

    if not token and not args.dry_run:
        print("error: Token cannot be empty.")
        sys.exit(1)

    print(f"==> Target Repository: {args.repo}")
    if args.dry_run:
        print("[-] Running in DRY RUN mode. No modifications will be made.")

    # 1. Update Repository Description
    print("\n--- 1. Repository 'About' Description & Homepage ---")
    repo_url = f"https://api.github.com/repos/{args.repo}"
    print(f"Description: {TARGET_DESCRIPTION}")
    print(f"Homepage:    {TARGET_HOMEPAGE}")
    if not args.dry_run:
        github_api_request(
            repo_url,
            method="PATCH",
            data={"description": TARGET_DESCRIPTION, "homepage": TARGET_HOMEPAGE},
            token=token,
        )
        print("✓ Repository description and homepage updated successfully.")

    # 2. Update Repository Topics
    print("\n--- 2. Repository Topics ---")
    print(f"Topics: {', '.join(TARGET_TOPICS)}")
    if not args.dry_run:
        topics_url = f"https://api.github.com/repos/{args.repo}/topics"
        github_api_request(
            topics_url,
            method="PUT",
            data={"names": TARGET_TOPICS},
            token=token,
        )
        print("✓ Repository topics updated successfully.")

    # 3. Update Existing Releases
    print("\n--- 3. Releases Notes ---")
    releases_data = load_release_notes()
    print(f"Loaded {len(releases_data)} release definitions from docs/GITHUB_RELEASES.md.")

    releases_api_url = f"https://api.github.com/repos/{args.repo}/releases?per_page=50"
    if args.dry_run and not token:
        # Query public API without token in dry-run
        req = urllib.request.Request(
            releases_api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Glyph-Metadata-Sync",
            },
        )
        with urllib.request.urlopen(req) as resp:
            remote_releases = json.loads(resp.read().decode("utf-8"))
    else:
        remote_releases = github_api_request(releases_api_url, token=token)

    print(f"Found {len(remote_releases)} existing releases on GitHub.")

    updated_count = 0
    for rel in remote_releases:
        tag = rel.get("tag_name")
        rel_id = rel.get("id")
        rel_name = rel.get("name")
        if tag in releases_data:
            new_body = releases_data[tag]
            target_name = f"Glyph - Text Extractor {tag}"
            print(f"\n[Release {tag}] (ID: {rel_id})")
            print(f"  Name: '{rel_name}' -> '{target_name}'")
            print(f"  Body length: {len(rel.get('body', ''))} -> {len(new_body)} characters")
            if not args.dry_run:
                update_url = f"https://api.github.com/repos/{args.repo}/releases/{rel_id}"
                github_api_request(
                    update_url,
                    method="PATCH",
                    data={"name": target_name, "body": new_body},
                    token=token,
                )
                print(f"  ✓ Updated {tag} successfully.")
            updated_count += 1
        else:
            print(f"\n[-] Skipping {tag}: Not found in docs/GITHUB_RELEASES.md")

    print(f"\n==> Finished. Total releases processed: {updated_count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        print(f"\nerror: {e}")
        sys.exit(1)
