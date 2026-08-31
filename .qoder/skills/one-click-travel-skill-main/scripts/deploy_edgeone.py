#!/usr/bin/env python3
"""Deploy a generated travel HTML page with the local EdgeOne CLI."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower()).strip("-")
    return slug or "travel-guide"


def prepare_publish_dir(html_path: Path, publish_dir: Path) -> Path:
    publish_dir.mkdir(parents=True, exist_ok=True)
    target = publish_dir / "index.html"
    shutil.copy2(html_path, target)
    return target


def extract_url(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("EDGEONE_DEPLOY_URL="):
            return line.split("=", 1)[1].strip()
    for match in URL_RE.findall(text):
        lowered = match.lower()
        if "edgeone" in lowered or "pages" in lowered:
            return match.rstrip(".,)")
    urls = URL_RE.findall(text)
    return urls[-1].rstrip(".,)") if urls else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True, help="Generated HTML file to publish.")
    parser.add_argument("--repo", default=".", help="Working directory used to create the publish folder.")
    parser.add_argument("--project-name", default="", help="EdgeOne Pages project name. Defaults to the HTML file stem.")
    parser.add_argument("--publish-dir", default="", help="Directory copied to EdgeOne. Defaults to output/edgeone/<project-name>.")
    parser.add_argument("--env", default="production", choices=["production", "preview"], help="EdgeOne deployment environment.")
    parser.add_argument("--dry-run", action="store_true", help="Prepare the publish folder but do not deploy.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    html_path = Path(args.html).resolve()
    project_name = slugify(args.project_name or html_path.stem)
    publish_dir = Path(args.publish_dir).resolve() if args.publish_dir else repo / "output" / "edgeone" / project_name

    result = {
        "deployed": False,
        "url": "",
        "local_path": str(html_path),
        "publish_dir": str(publish_dir),
        "project_name": project_name,
        "env": args.env,
        "action_required": "",
        "message": "",
    }

    if not html_path.exists():
        result["action_required"] = "fix_html_path"
        result["message"] = f"HTML file not found: {html_path}"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    index_path = prepare_publish_dir(html_path, publish_dir)
    result["local_path"] = str(index_path)

    if args.dry_run:
        result["action_required"] = "confirm_deploy"
        result["message"] = "Publish folder prepared. Run again without --dry-run to deploy with EdgeOne CLI."
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    edgeone = shutil.which("edgeone")
    if not edgeone:
        result["action_required"] = "install_edgeone_cli"
        result["message"] = "EdgeOne CLI is not installed. Install it with: npm install -g edgeone"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    command = [edgeone, "pages", "deploy", str(publish_dir), "-n", project_name, "-e", args.env]
    completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, timeout=600)
    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    result["message"] = output

    if completed.returncode == 0:
        result["deployed"] = True
        result["url"] = extract_url(output)
    else:
        lowered = output.lower()
        if "login" in lowered or "auth" in lowered or "unauthorized" in lowered:
            result["action_required"] = "edgeone_login"
        else:
            result["action_required"] = "inspect_cli_error"

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
