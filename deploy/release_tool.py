from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "deploy" / "release-manifest.json"
AGUSTA_DOC_PATH = ROOT / "agusta-doc"
PROJECT_REPOSITORY = "AdaptX/agusta"

KNOWN_SURFACES = {
    "cli_version",
    "compose_env_example",
    "quickstart_deployment_docs",
    "quickstart_upgrade_docs",
    "release_notes_pages",
    "vitepress_nav",
}


class ReleaseError(Exception):
    pass


@dataclass(frozen=True)
class Manifest:
    version: str
    title: str
    previous_version: str
    release_doc_slug: str
    release_docs_base_url: str
    surfaces: tuple[str, ...]
    base_tag: str | None = None

    @classmethod
    def load(cls) -> "Manifest":
        if not MANIFEST_PATH.exists():
            raise ReleaseError(f"Missing release manifest: {relative(MANIFEST_PATH)}")

        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        required = [
            "version",
            "title",
            "previousVersion",
            "releaseDocSlug",
            "releaseDocsBaseUrl",
            "surfaces",
        ]
        missing = [field for field in required if field not in data]
        if missing:
            raise ReleaseError(f"Missing release manifest fields: {', '.join(missing)}")

        surfaces = data["surfaces"]
        if not isinstance(surfaces, list) or not all(isinstance(item, str) for item in surfaces):
            raise ReleaseError("release-manifest.json field 'surfaces' must be a string list")

        unknown = sorted(set(surfaces) - KNOWN_SURFACES)
        if unknown:
            raise ReleaseError(f"Unknown release surfaces: {', '.join(unknown)}")

        version = str(data["version"])
        if version.startswith("v"):
            raise ReleaseError("release-manifest.json field 'version' must not start with 'v'")
        if len(version) > 128 or not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:[a-zA-Z0-9.-]*)?",
            version,
        ):
            raise ReleaseError(f"Unsupported release version format: {version!r}")

        previous_version = str(data["previousVersion"])
        if previous_version.startswith("v"):
            raise ReleaseError("release-manifest.json field 'previousVersion' must not start with 'v'")

        return cls(
            version=version,
            title=str(data["title"]),
            previous_version=previous_version,
            release_doc_slug=str(data["releaseDocSlug"]),
            release_docs_base_url=str(data["releaseDocsBaseUrl"]),
            surfaces=tuple(surfaces),
            base_tag=str(data["baseTag"]) if data.get("baseTag") else None,
        )

    @property
    def tag(self) -> str:
        return f"v{self.version}"

    @property
    def base_release_tag(self) -> str:
        return self.base_tag or f"v{self.previous_version}"

    @property
    def archive_name(self) -> str:
        return "agusta-compose.tar.gz"

    @property
    def release_doc_url(self) -> str:
        return f"{self.release_docs_base_url.rstrip('/')}/{self.release_doc_slug}/"

    @property
    def release_title(self) -> str:
        return f"{self.tag} - {self.title}"


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_if_changed(path: Path, content: str) -> None:
    old = read_text(path) if path.exists() else None
    if old == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"updated {relative(path)}")


def require_agusta_doc() -> None:
    if not (AGUSTA_DOC_PATH / "docs").is_dir():
        raise ReleaseError(
            "agusta-doc submodule is not initialized. Run: git submodule update --init agusta-doc"
        )


def github_repository() -> str:
    return os.environ.get("GITHUB_REPOSITORY", PROJECT_REPOSITORY)


def image_name(manifest: Manifest, image: str) -> str:
    repository = github_repository()
    if "/" not in repository:
        raise ReleaseError(f"Invalid GITHUB_REPOSITORY value: {repository!r}")
    owner, repo = repository.split("/", 1)
    return f"ghcr.io/{owner.lower()}/{repo.lower()}/{image}:{manifest.version}"


def project_release_url(manifest: Manifest) -> str:
    return f"https://github.com/{PROJECT_REPOSITORY}/releases/latest/download/{manifest.archive_name}"


def run_prepare(manifest: Manifest) -> None:
    for surface in manifest.surfaces:
        PREPARE_SURFACES[surface](manifest)
    run_check(manifest, tag=None)


def run_check(manifest: Manifest, tag: str | None) -> None:
    failures: list[str] = []
    if tag and tag != manifest.tag:
        failures.append(
            f"tag {tag!r} must match release manifest tag {manifest.tag!r}"
        )

    for surface in manifest.surfaces:
        CHECK_SURFACES[surface](manifest, failures)

    if failures:
        detail = "\n- ".join(failures)
        raise ReleaseError(f"Release consistency check failed:\n- {detail}")
    print("Release consistency check passed.")


def prepare_cli_version(manifest: Manifest) -> None:
    path = ROOT / "cli" / "pyproject.toml"
    text = read_text(path)
    new_text, count = re.subn(
        r'(?m)^version = "[^"]+"$',
        f'version = "{manifest.version}"',
        text,
        count=1,
    )
    if count != 1:
        raise ReleaseError(f"Could not find project version in {relative(path)}")
    write_text_if_changed(path, new_text)


def check_cli_version(manifest: Manifest, failures: list[str]) -> None:
    path = ROOT / "cli" / "pyproject.toml"
    try:
        version = tomllib.loads(read_text(path))["project"]["version"]
    except Exception as exc:
        failures.append(f"{relative(path)} cannot be parsed: {exc}")
        return
    if version != manifest.version:
        failures.append(
            f"{relative(path)} project.version is {version!r}, expected {manifest.version!r}"
        )


def prepare_compose_env_example(manifest: Manifest) -> None:
    path = ROOT / "deploy" / "agusta-compose" / ".env.example"
    text = read_text(path)
    replacements = {
        "AGUSTA_BACKEND_IMAGE": image_name(manifest, "agusta-backend"),
        "AGUSTA_FRONTEND_IMAGE": image_name(manifest, "agusta-frontend"),
    }
    for name, value in replacements.items():
        text, count = re.subn(
            rf"(?m)^{re.escape(name)}=.*$",
            f"{name}={value}",
            text,
            count=1,
        )
        if count != 1:
            raise ReleaseError(f"Could not find {name} in {relative(path)}")
    write_text_if_changed(path, text)


def check_compose_env_example(manifest: Manifest, failures: list[str]) -> None:
    path = ROOT / "deploy" / "agusta-compose" / ".env.example"
    lines = set(read_text(path).splitlines())
    expected = {
        f"AGUSTA_BACKEND_IMAGE={image_name(manifest, 'agusta-backend')}",
        f"AGUSTA_FRONTEND_IMAGE={image_name(manifest, 'agusta-frontend')}",
    }
    for line in sorted(expected - lines):
        failures.append(f"{relative(path)} missing expected line: {line}")


def generated_block(block_id: str, body: str) -> str:
    return f"<!-- {block_id}:start -->\n{body.rstrip()}\n<!-- {block_id}:end -->"


def replace_generated_block(text: str, block_id: str, replacement: str) -> tuple[str, int]:
    pattern = re.compile(
        rf"<!-- {re.escape(block_id)}:start -->.*?<!-- {re.escape(block_id)}:end -->",
        re.DOTALL,
    )
    return pattern.subn(replacement, text, count=1)


def ensure_generated_block(
    path: Path,
    block_id: str,
    expected: str,
    bootstrap: Callable[[str, str], str],
) -> None:
    text = read_text(path)
    new_text, count = replace_generated_block(text, block_id, expected)
    if count == 0:
        new_text = bootstrap(text, expected)
    write_text_if_changed(path, new_text)


def check_generated_block(
    path: Path,
    block_id: str,
    expected: str,
    failures: list[str],
) -> None:
    text = read_text(path)
    if expected not in text:
        failures.append(
            f"{relative(path)} generated block {block_id!r} is missing or stale; "
            "run python deploy/release_tool.py prepare"
        )


def deployment_block(manifest: Manifest, lang: str) -> str:
    url = project_release_url(manifest)
    if lang == "zh":
        body = f"""- GitHub Releases 页面：[https://github.com/{PROJECT_REPOSITORY}/releases](https://github.com/{PROJECT_REPOSITORY}/releases)
- 最新版本发布包：`{manifest.archive_name}`

```bash
curl -fL -o {manifest.archive_name} {url} &&
tar -xzf {manifest.archive_name} &&
rm {manifest.archive_name} &&
cd agusta-compose
```"""
    else:
        body = f"""- GitHub Releases: [https://github.com/{PROJECT_REPOSITORY}/releases](https://github.com/{PROJECT_REPOSITORY}/releases)
- Latest release package: `{manifest.archive_name}`

```bash
curl -fL -o {manifest.archive_name} {url} &&
tar -xzf {manifest.archive_name} &&
rm {manifest.archive_name} &&
cd agusta-compose
```"""
    return generated_block("release:deployment-package", body)


def bootstrap_deployment(lang: str) -> Callable[[str, str], str]:
    heading = "## 1. 下载发布包" if lang == "zh" else "## 1. Download the package"

    def bootstrap(text: str, expected: str) -> str:
        heading_index = text.find(heading)
        if heading_index < 0:
            raise ReleaseError(f"Could not find heading {heading!r} in deployment docs")
        body_start = heading_index + len(heading)
        next_index = text.find("\n## 2.", body_start)
        if next_index < 0:
            raise ReleaseError("Could not find deployment docs section boundary before step 2")
        return text[:body_start] + "\n\n" + expected + "\n" + text[next_index:]

    return bootstrap


def prepare_quickstart_deployment_docs(manifest: Manifest) -> None:
    require_agusta_doc()
    paths = {
        "zh": AGUSTA_DOC_PATH / "docs" / "zh" / "agusta" / "quick-start" / "deployment" / "index.md",
        "en": AGUSTA_DOC_PATH / "docs" / "en" / "agusta" / "quick-start" / "deployment" / "index.md",
    }
    for lang, path in paths.items():
        ensure_generated_block(
            path,
            "release:deployment-package",
            deployment_block(manifest, lang),
            bootstrap_deployment(lang),
        )


def check_quickstart_deployment_docs(manifest: Manifest, failures: list[str]) -> None:
    require_agusta_doc()
    paths = {
        "zh": AGUSTA_DOC_PATH / "docs" / "zh" / "agusta" / "quick-start" / "deployment" / "index.md",
        "en": AGUSTA_DOC_PATH / "docs" / "en" / "agusta" / "quick-start" / "deployment" / "index.md",
    }
    for lang, path in paths.items():
        check_generated_block(
            path,
            "release:deployment-package",
            deployment_block(manifest, lang),
            failures,
        )


def upgrade_block(manifest: Manifest, lang: str) -> str:
    url = project_release_url(manifest)
    if lang == "zh":
        body = f"""```bash
cd ..
curl -fL -o {manifest.archive_name} {url} &&
tar -xzf {manifest.archive_name} &&
rm {manifest.archive_name} &&
cd agusta-compose &&
./scripts/upgrade.sh
```"""
    else:
        body = f"""```bash
cd ..
curl -fL -o {manifest.archive_name} {url} &&
tar -xzf {manifest.archive_name} &&
rm {manifest.archive_name} &&
cd agusta-compose &&
./scripts/upgrade.sh
```"""
    return generated_block("release:managed-upgrade", body)


def bootstrap_upgrade(text: str, expected: str) -> str:
    old_generated_block = re.compile(
        r"<!-- release:upgrade-image-tags:start -->.*?<!-- release:upgrade-image-tags:end -->",
        re.DOTALL,
    )
    new_text, count = old_generated_block.subn(expected, text, count=1)
    if count == 1:
        return new_text

    pattern = re.compile(
        r"```text\n"
        r"AGUSTA_BACKEND_IMAGE=ghcr\.io/adaptx/agusta/agusta-backend:<version>\n"
        r"AGUSTA_FRONTEND_IMAGE=ghcr\.io/adaptx/agusta/agusta-frontend:<version>\n"
        r"```\n\n"
        r"(?:`<version>` 使用目标 Release 的版本号，例如 `[^`]+`。|"
        r"Use the target Release version for `<version>`, for example `[^`]+`\.)",
        re.MULTILINE,
    )
    new_text, count = pattern.subn(expected, text, count=1)
    if count != 1:
        raise ReleaseError("Could not find upgrade image tag example block")
    return new_text


def prepare_quickstart_upgrade_docs(manifest: Manifest) -> None:
    require_agusta_doc()
    paths = [
        AGUSTA_DOC_PATH / "docs" / "zh" / "agusta" / "quick-start" / "upgrade" / "index.md",
        AGUSTA_DOC_PATH / "docs" / "en" / "agusta" / "quick-start" / "upgrade" / "index.md",
    ]
    for path in paths:
        lang = "zh" if "\\zh\\" in str(path) or "/zh/" in str(path) else "en"
        ensure_generated_block(
            path,
            "release:managed-upgrade",
            upgrade_block(manifest, lang),
            bootstrap_upgrade,
        )


def check_quickstart_upgrade_docs(manifest: Manifest, failures: list[str]) -> None:
    require_agusta_doc()
    paths = [
        ("zh", AGUSTA_DOC_PATH / "docs" / "zh" / "agusta" / "quick-start" / "upgrade" / "index.md"),
        ("en", AGUSTA_DOC_PATH / "docs" / "en" / "agusta" / "quick-start" / "upgrade" / "index.md"),
    ]
    for lang, path in paths:
        check_generated_block(
            path,
            "release:managed-upgrade",
            upgrade_block(manifest, lang),
            failures,
        )


def release_page_skeleton(manifest: Manifest, lang: str) -> str:
    if lang == "zh":
        sections = [
            "新功能",
            "优化",
            "修复",
            "部署和发布工程",
            "升级说明",
            "开发者笔记",
        ]
    else:
        sections = [
            "New Features",
            "Improvements",
            "Fixes",
            "Deployment and Release Engineering",
            "Upgrade Notes",
            "Developer Notes",
        ]
    headings = "\n\n".join(f"## {section}\n" for section in sections)
    return f"# {manifest.version} - {manifest.title}\n\n{headings}\n"


def release_page_path(manifest: Manifest, lang: str) -> Path:
    return AGUSTA_DOC_PATH / "docs" / lang / "release" / manifest.release_doc_slug / "index.md"


def prepare_release_notes_pages(manifest: Manifest) -> None:
    require_agusta_doc()
    for lang in ("zh", "en"):
        path = release_page_path(manifest, lang)
        if not path.exists():
            write_text_if_changed(path, release_page_skeleton(manifest, lang))


def check_release_notes_pages(manifest: Manifest, failures: list[str]) -> None:
    require_agusta_doc()
    expected_title = f"# {manifest.version} - {manifest.title}"
    for lang in ("zh", "en"):
        path = release_page_path(manifest, lang)
        if not path.exists():
            failures.append(f"Missing release notes page: {relative(path)}")
            continue
        first_line = read_text(path).splitlines()[0] if read_text(path).splitlines() else ""
        if first_line != expected_title:
            failures.append(
                f"{relative(path)} title is {first_line!r}, expected {expected_title!r}"
            )


def nav_item(manifest: Manifest, lang: str) -> str:
    link = (
        f"/zh/release/{manifest.release_doc_slug}/"
        if lang == "zh"
        else f"/release/{manifest.release_doc_slug}/"
    )
    return (
        "                {\n"
        f"                    text: '{manifest.version} - {manifest.title}',\n"
        f"                    link: '{link}'\n"
        "                },"
    )


def remove_current_nav_items(text: str, manifest: Manifest, lang: str) -> str:
    prefix = "/zh/release/" if lang == "zh" else "/release/"
    pattern = re.compile(
        r"\n                \{\n"
        rf"                    text: '{re.escape(manifest.version)} - [^']+',\n"
        rf"                    link: '{re.escape(prefix)}[^']+/'\n"
        r"                \},?",
    )
    return pattern.sub("", text)


def prepare_vitepress_nav(manifest: Manifest) -> None:
    require_agusta_doc()
    paths = {
        "zh": AGUSTA_DOC_PATH / "docs" / ".vitepress" / "config" / "zh.ts",
        "en": AGUSTA_DOC_PATH / "docs" / ".vitepress" / "config" / "en.ts",
    }
    labels = {"zh": 'text: "更新日志"', "en": 'text: "Changelog"'}
    for lang, path in paths.items():
        text = read_text(path)
        expected = nav_item(manifest, lang)
        if expected in text:
            continue
        text = remove_current_nav_items(text, manifest, lang)
        label_index = text.find(labels[lang])
        if label_index < 0:
            raise ReleaseError(f"Could not find changelog nav label in {relative(path)}")
        items_index = text.find("items: [", label_index)
        if items_index < 0:
            raise ReleaseError(f"Could not find changelog items array in {relative(path)}")
        insert_index = text.find("\n", items_index)
        if insert_index < 0:
            raise ReleaseError(f"Could not find insertion point in {relative(path)}")
        text = text[: insert_index + 1] + expected + "\n" + text[insert_index + 1 :]
        write_text_if_changed(path, text)


def check_vitepress_nav(manifest: Manifest, failures: list[str]) -> None:
    require_agusta_doc()
    paths = {
        "zh": AGUSTA_DOC_PATH / "docs" / ".vitepress" / "config" / "zh.ts",
        "en": AGUSTA_DOC_PATH / "docs" / ".vitepress" / "config" / "en.ts",
    }
    for lang, path in paths.items():
        if nav_item(manifest, lang) not in read_text(path):
            failures.append(
                f"{relative(path)} missing changelog nav item for {manifest.version}"
            )


PREPARE_SURFACES: dict[str, Callable[[Manifest], None]] = {
    "cli_version": prepare_cli_version,
    "compose_env_example": prepare_compose_env_example,
    "quickstart_deployment_docs": prepare_quickstart_deployment_docs,
    "quickstart_upgrade_docs": prepare_quickstart_upgrade_docs,
    "release_notes_pages": prepare_release_notes_pages,
    "vitepress_nav": prepare_vitepress_nav,
}

CHECK_SURFACES: dict[str, Callable[[Manifest, list[str]], None]] = {
    "cli_version": check_cli_version,
    "compose_env_example": check_compose_env_example,
    "quickstart_deployment_docs": check_quickstart_deployment_docs,
    "quickstart_upgrade_docs": check_quickstart_upgrade_docs,
    "release_notes_pages": check_release_notes_pages,
    "vitepress_nav": check_vitepress_nav,
}


def show(manifest: Manifest, output_format: str) -> None:
    values = {
        "version": manifest.version,
        "tag": manifest.tag,
        "base_tag": manifest.base_release_tag,
        "title": manifest.title,
        "release_title": manifest.release_title,
        "release_doc_slug": manifest.release_doc_slug,
        "release_doc_url": manifest.release_doc_url,
        "archive_name": manifest.archive_name,
        "backend_image": image_name(manifest, "agusta-backend"),
        "frontend_image": image_name(manifest, "agusta-frontend"),
    }
    if output_format == "json":
        print(json.dumps(values, indent=2, ensure_ascii=False))
    elif output_format == "github-output":
        for key, value in values.items():
            print(f"{key}={value}")
    else:
        for key, value in values.items():
            print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and validate AGUSTA release files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare", help="Update deterministic release files from the manifest.")

    check_parser = subparsers.add_parser("check", help="Validate release files against the manifest.")
    check_parser.add_argument("--tag", help="Optional pushed tag to compare with the manifest version.")

    show_parser = subparsers.add_parser("show", help="Print derived release values.")
    show_parser.add_argument(
        "--format",
        choices=("human", "json", "github-output"),
        default="human",
        help="Output format.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        manifest = Manifest.load()
        if args.command == "prepare":
            run_prepare(manifest)
        elif args.command == "check":
            run_check(manifest, tag=args.tag)
        elif args.command == "show":
            show(manifest, output_format=args.format)
        else:
            parser.error(f"Unknown command: {args.command}")
    except ReleaseError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
