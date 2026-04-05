#!/usr/bin/env python3
"""
SkillLoader SDK
---------------
Unified skill catalog and CLI for discovering, searching, and loading skills.
Single source of truth: .gemini/skills/

Usage:
    python skills_sdk.py list
    python skills_sdk.py list --category engineering
    python skills_sdk.py search "code review"
    python skills_sdk.py info systematic-debugging
    python skills_sdk.py categories
    python skills_sdk.py export [--output catalog.json]

  skills.sh integration (requires npx):
    python skills_sdk.py browse [query]
    python skills_sdk.py install <owner/repo>
    python skills_sdk.py install <owner/repo@skill-name>
    python skills_sdk.py install <owner/repo> --skill frontend-design tdd-workflow
    python skills_sdk.py install --list <owner/repo>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
# SKILLLOADER_HOME lets the script work from any location (e.g. ~/bin/)
ROOT        = Path(os.environ.get("SKILLLOADER_HOME", Path(__file__).parent)).expanduser().resolve()
SKILLS_DIR  = ROOT / ".gemini" / "skills"
INDEX_FILE  = ROOT / ".gemini" / "skills-index.json"

# ── Category taxonomy ─────────────────────────────────────────────────────────
CATEGORIES: dict[str, str] = {
    "agent":                "Persona-based agents (cs-*, devops, PM, CTO…)",
    "c-level":              "C-suite advisory (CEO/CTO/CFO/CMO advisors, board)",
    "engineering":          "Core software engineering (code review, TDD, git, CI/CD)",
    "engineering-advanced": "Advanced patterns (agents, AI, multi-agent, context)",
    "marketing":            "Marketing, SEO, content, paid ads, CRO",
    "product":              "Product management, strategy, discovery",
    "business-growth":      "Sales, revenue ops, customer success",
    "finance":              "Financial analysis, modeling, SaaS metrics",
    "project-management":   "Agile, Jira, Confluence, Scrum, OKRs",
    "ra-qm":                "Quality, regulatory, compliance (ISO, FDA, GDPR)",
    "command":              "Slash-command utilities and shortcuts",
    "document":             "Document creation / manipulation (docx, pdf, xlsx, pptx)",
    "workflow":             "Planning, execution, collaboration workflows",
}

# ── Manual overrides for skills not in the index ─────────────────────────────
# (antigravity + openCode skills that were merged into .gemini/skills/)
MANUAL_CATEGORIES: dict[str, str] = {
    # antigravity
    "advanced-evaluation":            "engineering-advanced",
    "algorithmic-art":                "engineering-advanced",
    "bdi-mental-states":              "engineering-advanced",
    "brainstorming":                  "product",
    "brand-guidelines":               "marketing",
    "canvas-design":                  "engineering-advanced",
    "context-compression":            "engineering-advanced",
    "context-degradation":            "engineering-advanced",
    "context-fundamentals":           "engineering-advanced",
    "context-optimization":           "engineering-advanced",
    "dispatching-parallel-agents":    "engineering-advanced",
    "doc-coauthoring":                "workflow",
    "docx":                           "document",
    "evaluation":                     "engineering-advanced",
    "executing-plans":                "workflow",
    "filesystem-context":             "engineering-advanced",
    "finishing-a-development-branch": "engineering",
    "frontend-design":                "engineering",
    "hosted-agents":                  "engineering-advanced",
    "internal-comms":                 "command",
    "json-canvas":                    "document",
    "mcp-builder":                    "engineering",
    "memory-systems":                 "engineering-advanced",
    "multi-agent-patterns":           "engineering-advanced",
    "notebooklm":                     "command",
    "obsidian-bases":                 "document",
    "obsidian-markdown":              "document",
    "pdf":                            "document",
    "planning-with-files":            "workflow",
    "pptx":                           "document",
    "project-development":            "engineering-advanced",
    "receiving-code-review":          "engineering",
    "remotion":                       "engineering",
    "requesting-code-review":         "engineering",
    "skill-creator":                  "command",
    "slack-gif-creator":              "command",
    "subagent-driven-development":    "engineering-advanced",
    "systematic-debugging":           "engineering",
    "test-driven-development":        "engineering",
    "theme-factory":                  "engineering",
    "tool-design":                    "engineering-advanced",
    "ui-ux-pro-max":                  "engineering",
    "using-git-worktrees":            "engineering",
    "using-superpowers":              "command",
    "verification-before-completion": "engineering",
    "web-artifacts-builder":          "engineering",
    "webapp-testing":                 "engineering",
    "writing-plans":                  "workflow",
    "writing-skills":                 "command",
    "xlsx":                           "document",
    # misc bundles / copies
    "brand-guidelines copy":  "marketing",
    "c-level-advisor-main":   "c-level",
    "engineering-main":       "engineering",
    "marketing-bundle":       "marketing",
    "product-bundle":         "product",
    "ra-qm-team-main":        "ra-qm",
    # openCode
    "api-design":             "engineering",
    "article-writing":        "marketing",
    "backend-patterns":       "engineering",
    "bun-runtime":            "engineering",
    "claude-api":             "engineering",
    "coding-standards":       "engineering",
    "content-engine":         "marketing",
    "crosspost":              "marketing",
    "deep-research":          "engineering-advanced",
    "dmux-workflows":         "engineering-advanced",
    "documentation-lookup":   "engineering",
    "e2e-testing":            "engineering",
    "eval-harness":           "engineering-advanced",
    "everything-claude-code": "command",
    "exa-search":             "engineering-advanced",
    "fal-ai-media":           "engineering",
    "frontend-patterns":      "engineering",
    "frontend-slides":        "engineering",
    "investor-materials":     "finance",
    "investor-outreach":      "business-growth",
    "market-research":        "marketing",
    "mcp-server-patterns":    "engineering",
    "nextjs-turbopack":       "engineering",
    "security-review":        "engineering",
    "strategic-compact":      "c-level",
    "tdd-workflow":           "engineering",
    "verification-loop":      "engineering",
    "video-editing":          "engineering",
    "x-api":                  "engineering",
}


# ─────────────────────────────────────────────────────────────────────────────
# Catalog building
# ─────────────────────────────────────────────────────────────────────────────

def _load_index() -> dict[str, dict]:
    """Load skills-index.json into a name → {category, description} map."""
    if not INDEX_FILE.exists():
        return {}
    with INDEX_FILE.open() as f:
        data = json.load(f)
    result = {}
    for entry in data.get("skills", []):
        name = entry.get("name", "")
        if name in ("README", "TEMPLATE"):
            continue
        result[name] = {
            "category": entry.get("category", "general"),
            "description": entry.get("description", ""),
        }
    return result


def _parse_skill_md(skill_md: Path) -> dict:
    """Extract name/description from a SKILL.md frontmatter."""
    name = skill_md.parent.name
    description = ""
    try:
        text = skill_md.read_text(errors="replace")
        lines = text.splitlines()
        in_front = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---":
                in_front = not in_front
                continue
            if in_front:
                if stripped.startswith("name:"):
                    name = stripped[5:].strip()
                elif stripped.startswith("description:"):
                    description = stripped[12:].strip()
            elif not description and stripped and not stripped.startswith("#"):
                description = stripped[:200]
    except OSError:
        pass
    return {"name": name, "description": description}


def build_catalog() -> dict:
    """Build the unified skill catalog by scanning .gemini/skills/."""
    index = _load_index()
    skills: list[dict] = []
    seen: set[str] = set()

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_name = skill_dir.name
        if skill_name in ("README", "TEMPLATE", "skill_files.txt"):
            continue
        if skill_name in seen:
            continue
        seen.add(skill_name)

        skill_md = skill_dir / "SKILL.md"

        # Description: prefer index, then parse SKILL.md
        if skill_name in index:
            description = index[skill_name]["description"]
        elif skill_md.exists():
            description = _parse_skill_md(skill_md)["description"]
        else:
            description = ""

        # Category: index first, then manual override, then "general"
        if skill_name in index:
            category = index[skill_name]["category"]
        else:
            category = MANUAL_CATEGORIES.get(skill_name, "general")

        skills.append({
            "name": skill_name,
            "category": category,
            "description": description,
            "path": str(skill_dir),
        })

    skills.sort(key=lambda s: (s["category"], s["name"]))

    return {
        "version": "1.0.0",
        "name": "skillloader-catalog",
        "total_skills": len(skills),
        "categories": CATEGORIES,
        "skills": skills,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_categories(catalog: dict, _args) -> None:
    counts: dict[str, int] = {}
    for s in catalog["skills"]:
        c = s["category"]
        counts[c] = counts.get(c, 0) + 1

    print(f"\n{'Category':<26} {'Skills':>6}  Description")
    print("─" * 80)
    for cat, desc in CATEGORIES.items():
        n = counts.get(cat, 0)
        print(f"  {cat:<24} {n:>6}  {desc}")

    for cat in sorted(counts):
        if cat not in CATEGORIES:
            print(f"  {cat:<24} {counts[cat]:>6}  (unlisted)")

    print(f"\n  Total: {catalog['total_skills']} skills\n")


def cmd_list(catalog: dict, args) -> None:
    skills = catalog["skills"]
    if hasattr(args, "category") and args.category:
        target = args.category.lower()
        skills = [s for s in skills if s["category"] == target]
        if not skills:
            print(f"No skills found for category '{target}'.")
            return

    cur_cat = None
    for s in skills:
        if s["category"] != cur_cat:
            cur_cat = s["category"]
            label = CATEGORIES.get(cur_cat, cur_cat)
            print(f"\n── {cur_cat.upper()} ── {label}")
        desc = s["description"][:70] + ("…" if len(s["description"]) > 70 else "")
        print(f"   {s['name']:<40}  {desc}")

    print(f"\n  {len(skills)} skill(s) listed.\n")


def cmd_search(catalog: dict, args) -> None:
    query = args.query.lower()
    results = [
        s for s in catalog["skills"]
        if query in s["name"].lower() or query in s["description"].lower()
    ]
    if not results:
        print(f"No results for '{args.query}'.")
        return

    print(f"\nResults for '{args.query}':\n")
    for s in results:
        desc = s["description"][:80] + ("…" if len(s["description"]) > 80 else "")
        print(f"  [{s['category']}]  {s['name']}")
        print(f"      {desc}\n")
    print(f"  {len(results)} result(s).\n")


def cmd_info(catalog: dict, args) -> None:
    target = args.skill.lower()
    matches = [s for s in catalog["skills"] if s["name"].lower() == target]
    if not matches:
        matches = [s for s in catalog["skills"] if target in s["name"].lower()]
    if not matches:
        print(f"Skill '{args.skill}' not found. Try `search` instead.")
        return

    for s in matches:
        print(f"\n  Name        : {s['name']}")
        print(f"  Category    : {s['category']}  ({CATEGORIES.get(s['category'], '')})")
        print(f"  Path        : {s['path']}")
        print(f"  Description : {s['description']}\n")
        skill_md = Path(s["path"]) / "SKILL.md"
        if skill_md.exists():
            print(f"  SKILL.md    : {skill_md}\n")


def _require_npx() -> str:
    """Return path to npx or exit with a helpful message."""
    npx = shutil.which("npx")
    if not npx:
        print("Error: 'npx' not found. Install Node.js from https://nodejs.org/")
        sys.exit(1)
    return npx


def cmd_browse(catalog: dict, args) -> None:
    """Search skills.sh registry via `npx skills find`."""
    npx = _require_npx()
    query = getattr(args, "query", None) or ""
    cmd = [npx, "skills", "find"]
    if query:
        cmd.append(query)
    # Run in ROOT so relative paths resolve correctly
    subprocess.run(cmd, cwd=str(ROOT))


def cmd_install(catalog: dict, args) -> None:
    """
    Install skills from skills.sh into .gemini/skills/ via `npx skills add`.

    Examples
    --------
    # Install all skills from a repo
    python skills_sdk.py install vercel-labs/agent-skills

    # Install specific skills from a repo
    python skills_sdk.py install obra/superpowers --skill systematic-debugging tdd-workflow

    # Install a single skill using shorthand  owner/repo@skill
    python skills_sdk.py install obra/superpowers@requesting-code-review

    # List available skills in a repo without installing
    python skills_sdk.py install vercel-labs/agent-skills --list
    """
    npx = _require_npx()
    source: str = args.source

    cmd = [npx, "skills", "add", source,
           "--agent", "gemini",   # targets .gemini/skills/
           "--copy",              # copy files instead of symlinks
           "--yes"]               # skip interactive prompts

    if getattr(args, "list_only", False):
        cmd.append("--list")

    if getattr(args, "skill", None):
        for s in args.skill:
            cmd += ["--skill", s]

    print(f"Running: {' '.join(cmd)}")
    print(f"Target : {SKILLS_DIR}\n")

    result = subprocess.run(cmd, cwd=str(ROOT))

    if result.returncode == 0 and not getattr(args, "list_only", False):
        print(f"\nDone. Run `python skills_sdk.py categories` to see the updated catalog.")


def _real_src(skill_dir: Path) -> Path:
    """
    Return the actual directory to copy from.

    Skills from claude-skills/ are stored in .gemini/skills/ as directories
    whose SKILL.md is a symlink relative to claude-skills/.gemini/skills/.
    When .gemini/ lives at the repo root those symlinks are broken.
    Reconstruct the real path by resolving relative to claude-skills/.
    """
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        return skill_dir          # real file — antigravity / openCode skills
    if skill_md.is_symlink():
        link = Path(os.readlink(skill_md))
        fake_base = ROOT / "claude-skills" / ".gemini" / "skills" / skill_dir.name
        real = (fake_base / link).resolve()
        if real.exists():
            return real.parent    # claude-skills/subdir/skill-name/
    return skill_dir              # fallback


def _pick(prompt: str, options: list[str], multi: bool = True) -> list[str]:
    """
    Interactive numbered picker.
    Returns selected items. Type numbers like: 1,3,5  or  1-4  or  all
    """
    for i, opt in enumerate(options, 1):
        print(f"  {i:>3})  {opt}")
    print()

    while True:
        raw = input(f"{prompt} ('all' for everything, 'q' to quit): ").strip().lower()
        if raw == "q":
            print("Aborted.")
            sys.exit(0)
        if raw == "all":
            return options

        selected = []
        valid = True
        for part in raw.replace(" ", "").split(","):
            if "-" in part:
                try:
                    lo, hi = part.split("-", 1)
                    for n in range(int(lo), int(hi) + 1):
                        if 1 <= n <= len(options):
                            selected.append(options[n - 1])
                        else:
                            valid = False
                except ValueError:
                    valid = False
            else:
                try:
                    n = int(part)
                    if 1 <= n <= len(options):
                        selected.append(options[n - 1])
                    else:
                        valid = False
                except ValueError:
                    valid = False

        if valid and selected:
            if not multi:
                return [selected[0]]
            return selected
        print(f"  Invalid input. Enter numbers 1-{len(options)}, ranges (1-3), or 'all'.\n")


AGENT_FOLDERS = {
    "Claude":     ".claude",
    "Gemini":     ".gemini",
    "Agent":      ".agent",
    "Codex":      ".codex",
    "OpenCode":   ".opencode",
    "Windsurf":   ".windsurf",
    "Cursor":     ".cursor",
}


def cmd_deploy(catalog: dict, args) -> None:
    """
    Interactively pick categories + skills and copy them to a project.

    Usage:
        python skills_sdk.py deploy                  # targets current directory
        python skills_sdk.py deploy /path/to/project
    """
    target_root = Path(getattr(args, "project", None) or os.getcwd()).resolve()

    print(f"\n{'─'*50}")
    print(f"  SkillLoader  →  Deploy to project")
    print(f"  Target: {target_root}")
    print(f"{'─'*50}\n")

    # ── Step 1: pick agent ────────────────────────────────────────────────────
    print("Step 1 — Choose agent folder:\n")
    agent_names = list(AGENT_FOLDERS.keys())
    chosen_agents = _pick("Agent", agent_names, multi=False)
    agent_folder = AGENT_FOLDERS[chosen_agents[0]]
    dest_skills = target_root / agent_folder / "skills"
    print(f"\n  → {dest_skills}\n")

    # ── Step 2: pick categories ───────────────────────────────────────────────
    # Build category list that has skills
    cat_counts: dict[str, int] = {}
    for s in catalog["skills"]:
        c = s["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # Show defined categories first, then any unlisted ones
    ordered_cats = [c for c in CATEGORIES if c in cat_counts]
    for c in sorted(cat_counts):
        if c not in ordered_cats:
            ordered_cats.append(c)

    cat_labels = [f"{c:<26} ({cat_counts[c]} skills)  {CATEGORIES.get(c, '')}" for c in ordered_cats]

    print("Step 2 — Choose categories:\n")
    chosen_labels = _pick("Categories (e.g. 1,3 or 1-4)", cat_labels, multi=True)
    chosen_cats = [ordered_cats[cat_labels.index(lbl)] for lbl in chosen_labels]
    print()

    # ── Step 3: pick skills within each chosen category ───────────────────────
    selected_skills: list[dict] = []

    for cat in chosen_cats:
        cat_skills = [s for s in catalog["skills"] if s["category"] == cat]
        label = CATEGORIES.get(cat, cat)
        print(f"Step 3 — {cat.upper()}  ({label}):\n")

        skill_names = [s["name"] for s in cat_skills]
        # Show name + truncated description inline
        display = []
        for s in cat_skills:
            desc = s["description"][:55] + ("…" if len(s["description"]) > 55 else "")
            display.append(f"{s['name']:<38}  {desc}")

        chosen_display = _pick(f"Skills from {cat}", display, multi=True)
        chosen_indices = [display.index(d) for d in chosen_display]
        selected_skills.extend(cat_skills[i] for i in chosen_indices)
        print()

    if not selected_skills:
        print("Nothing selected. Exiting.")
        return

    # ── Step 4: copy ──────────────────────────────────────────────────────────
    print(f"{'─'*50}")
    print(f"  Copying {len(selected_skills)} skill(s) to {dest_skills}")
    print(f"{'─'*50}\n")

    dest_skills.mkdir(parents=True, exist_ok=True)
    ok = []
    failed = []

    for skill in selected_skills:
        src = _real_src(Path(skill["path"]))
        dst = dest_skills / skill["name"]
        try:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            ok.append(skill["name"])
            print(f"  ✓  {skill['name']}")
        except Exception as e:
            failed.append(skill["name"])
            print(f"  ✗  {skill['name']}  ({e})")

    print(f"\n  Done — {len(ok)} copied", end="")
    if failed:
        print(f", {len(failed)} failed: {', '.join(failed)}", end="")
    print(f"\n  Location: {dest_skills}\n")


def cmd_export(catalog: dict, args) -> None:
    output = Path(getattr(args, "output", None) or ROOT / "skills-catalog.json")
    output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"Catalog written to {output}  ({catalog['total_skills']} skills)")


# ─────────────────────────────────────────────────────────────────────────────
# Public API (importable)
# ─────────────────────────────────────────────────────────────────────────────

def get_catalog() -> dict:
    return build_catalog()


def list_skills(category: Optional[str] = None) -> list[dict]:
    skills = build_catalog()["skills"]
    if category:
        skills = [s for s in skills if s["category"] == category]
    return skills


def search_skills(query: str) -> list[dict]:
    q = query.lower()
    return [
        s for s in build_catalog()["skills"]
        if q in s["name"].lower() or q in s["description"].lower()
    ]


def get_skill(name: str) -> Optional[dict]:
    n = name.lower()
    for s in build_catalog()["skills"]:
        if s["name"].lower() == n:
            return s
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="skills_loader",
        description="SkillLoader — deploy and manage SKILL.md skills.\nRun with no arguments to deploy skills into the current project.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("categories", help="List all categories with skill counts")

    p_list = sub.add_parser("list", help="List skills (optionally by category)")
    p_list.add_argument("--category", "-c", help="Filter by category slug")

    p_search = sub.add_parser("search", help="Full-text search across all skills")
    p_search.add_argument("query", help="Search term")

    p_info = sub.add_parser("info", help="Show details for a specific skill")
    p_info.add_argument("skill", help="Skill name")

    p_export = sub.add_parser("export", help="Export catalog to JSON")
    p_export.add_argument("--output", "-o", help="Output file path")

    # deploy
    p_deploy = sub.add_parser(
        "deploy",
        help="Interactively pick skills and copy them to a project",
    )
    p_deploy.add_argument(
        "project", nargs="?",
        help="Path to target project (default: current directory)",
    )

    # skills.sh commands
    p_browse = sub.add_parser("browse", help="Search skills.sh registry (requires npx)")
    p_browse.add_argument("query", nargs="?", help="Search query (omit for interactive mode)")

    p_install = sub.add_parser(
        "install",
        help="Install skills from skills.sh into .gemini/skills/ (requires npx)",
        description=(
            "Install skills from a GitHub repo via skills.sh.\n\n"
            "Examples:\n"
            "  python skills_sdk.py install vercel-labs/agent-skills\n"
            "  python skills_sdk.py install obra/superpowers --skill systematic-debugging\n"
            "  python skills_sdk.py install obra/superpowers@requesting-code-review\n"
            "  python skills_sdk.py install vercel-labs/agent-skills --list\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_install.add_argument("source", help="owner/repo or owner/repo@skill-name")
    p_install.add_argument(
        "--skill", "-s", nargs="+", metavar="SKILL",
        help="Pick specific skill name(s) from the repo",
    )
    p_install.add_argument(
        "--list", "-l", dest="list_only", action="store_true",
        help="List available skills in repo without installing",
    )

    args = parser.parse_args()

    # Default: deploy to current directory
    if not args.command:
        args.command = "deploy"
        args.project = None

    catalog = build_catalog()

    dispatch = {
        "categories": cmd_categories,
        "list":       cmd_list,
        "search":     cmd_search,
        "info":       cmd_info,
        "export":     cmd_export,
        "browse":     cmd_browse,
        "install":    cmd_install,
        "deploy":     cmd_deploy,
    }
    dispatch[args.command](catalog, args)


if __name__ == "__main__":
    main()
