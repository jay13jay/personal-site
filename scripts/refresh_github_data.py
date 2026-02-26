#!/usr/bin/env python3

import argparse
import collections
import datetime
import json
import pathlib
import subprocess
import sys


def run_gh_api(args: list[str]) -> dict | list:
    cmd = ["gh", "api", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gh api call failed")
    return json.loads(result.stdout)


def escape_toml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def toml_line(key: str, value) -> str:
    if isinstance(value, bool):
        return f"{key} = {'true' if value else 'false'}"
    if isinstance(value, int):
        return f"{key} = {value}"
    return f'{key} = "{escape_toml(str(value))}"'


def build_toml(profile: dict, pinned_nodes: list[dict], language_counts: list[tuple[str, int]]) -> str:
    lines: list[str] = []
    lines.append("[profile]")
    profile_keys = [
        "login",
        "name",
        "company",
        "location",
        "bio",
        "html_url",
        "public_repos",
        "followers",
        "following",
        "updated_at",
    ]

    for key in profile_keys:
        value = profile.get(key, "")
        if value is None:
            value = ""
        lines.append(toml_line(key, value))

    generated_at = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines.append(toml_line("generated_at", generated_at))

    for repo in pinned_nodes:
        lines.append("")
        lines.append("[[pinned]]")
        lines.append(toml_line("name", repo.get("name", "")))
        lines.append(toml_line("name_with_owner", repo.get("nameWithOwner", "")))
        lines.append(toml_line("description", repo.get("description") or ""))
        lines.append(toml_line("url", repo.get("url", "")))
        lines.append(toml_line("stars", int(repo.get("stargazerCount", 0))))
        lines.append(toml_line("forks", int(repo.get("forkCount", 0))))
        primary_language = ((repo.get("primaryLanguage") or {}).get("name") or "")
        lines.append(toml_line("primary_language", primary_language))

    for name, count in language_counts:
        lines.append("")
        lines.append("[[languages]]")
        lines.append(toml_line("name", name))
        lines.append(toml_line("count", count))

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh public GitHub data for Hugo templates.")
    parser.add_argument("--user", required=True, help="GitHub username")
    parser.add_argument("--out", default="data/en/github.toml", help="Output TOML path")
    args = parser.parse_args()

    user = args.user

    profile_raw = run_gh_api([f"users/{user}"])
    profile = {
        "login": profile_raw.get("login", ""),
        "name": profile_raw.get("name") or "",
        "company": profile_raw.get("company") or "",
        "location": profile_raw.get("location") or "",
        "bio": profile_raw.get("bio") or "",
        "html_url": profile_raw.get("html_url", ""),
        "public_repos": int(profile_raw.get("public_repos", 0)),
        "followers": int(profile_raw.get("followers", 0)),
        "following": int(profile_raw.get("following", 0)),
        "updated_at": profile_raw.get("updated_at", ""),
    }

    query = (
        "query($login:String!){"
        " user(login:$login){"
        "   pinnedItems(first:6, types: REPOSITORY){"
        "     nodes {"
        "       ... on Repository {"
        "         name nameWithOwner description url stargazerCount forkCount primaryLanguage { name }"
        "       }"
        "     }"
        "   }"
        " }"
        "}"
    )
    graphql = run_gh_api(["graphql", "-f", f"query={query}", "-F", f"login={user}"])
    pinned_nodes = (((graphql.get("data") or {}).get("user") or {}).get("pinnedItems") or {}).get("nodes") or []

    repos = run_gh_api([f"users/{user}/repos?per_page=100&type=owner", "--paginate"])
    language_counter: collections.Counter[str] = collections.Counter()
    for repo in repos:
        if repo.get("fork"):
            continue
        language = repo.get("language")
        if language:
            language_counter[language] += 1

    language_counts = sorted(language_counter.items(), key=lambda item: (-item[1], item[0]))

    output_path = pathlib.Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_toml(profile, pinned_nodes, language_counts), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
