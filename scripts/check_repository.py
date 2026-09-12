"""Check local Markdown destinations and language pairs without network access."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", path.read_text(encoding="utf-8"), re.MULTILINE):
        base = re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
        count = counts.get(base, 0)
        counts[base] = count + 1
        found.add(f"{base}-{count}" if count else base)
    return found


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pairs = [("README.md", "README.zh-CN.md")]
    pairs += [(f"docs/{name}.md", f"docs/{name}.zh-CN.md")
              for name in ("installation", "api", "protocol", "architecture", "performance")]
    for pair in pairs:
        assert all((root / path).is_file() for path in pair), f"Missing language pair: {pair}"
    files = [*root.glob("*.md"), *root.joinpath("docs").rglob("*.md"),
             root / "game/UPSTREAM.md", root / "game/LOCAL_CHANGES.md"]
    errors: list[str] = []
    for path in files:
        content = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for target in re.findall(r"\[[^\]\n]*\]\(([^\s)]+)\)", content):
            link = urlsplit(target)
            if link.scheme or link.netloc:
                continue
            destination = (path.parent / unquote(link.path)).resolve() if link.path else path
            if not destination.exists():
                errors.append(f"{path.relative_to(root)}: missing {target}")
            elif link.fragment and destination.suffix == ".md" and unquote(link.fragment) not in anchors(destination):
                errors.append(f"{path.relative_to(root)}: missing anchor {target}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(files)} Markdown files and {len(pairs)} language pairs (local links only)")


if __name__ == "__main__":
    main()
