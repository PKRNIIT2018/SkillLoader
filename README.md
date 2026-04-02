# SkillLoader SDK

A unified skill library and CLI for discovering, deploying, and managing [SKILL.md](https://agentskills.io) skills across AI coding agents — Claude Code, Gemini CLI, Codex, Cursor, OpenCode, and more.

**344 curated skills** across 13 categories, plus live integration with the [skills.sh](https://skills.sh) registry (91,500+ skills).

---

## Requirements

- Python 3.8+
- Node.js / npx — required only for `browse` and `install` commands

---

## Setup

```bash
git clone --recurse-submodules https://github.com/<you>/SkillLoader.git
cd SkillLoader
```

> `--recurse-submodules` pulls `claude-skills/` which backs the skill library.

---

## Commands

### Explore your local library

```bash
# See all 13 categories with skill counts
python skills_sdk.py categories

# List skills in a category
python skills_sdk.py list --category engineering
python skills_sdk.py list -c marketing

# Full-text search
python skills_sdk.py search "code review"
python skills_sdk.py search "stripe"

# Details on one skill
python skills_sdk.py info systematic-debugging
```

### Deploy skills to a project

Interactively pick agent → categories → individual skills, then copy to any project:

```bash
python skills_sdk.py deploy /path/to/your-project
python skills_sdk.py deploy          # targets current directory
```

Example session:
```
Step 1 — Choose agent folder:
     1)  Claude     (.claude/skills/)
     2)  Gemini     (.gemini/skills/)
     ...

Step 2 — Choose categories:
     5)  marketing    (50 skills)
     3)  engineering  (77 skills)
  > 5

Step 3 — MARKETING:
     3)  ai-seo          AI-first SEO strategy…
     7)  analytics-tracking  …
  > 3,7,12    (or "all", or ranges like 1-5)

  ✓ ai-seo
  ✓ analytics-tracking
  ✓ seo-audit
  Done — 3 copied → your-project/.claude/skills/
```

### Pull new skills from skills.sh registry

```bash
# Search 91,500+ skills
python skills_sdk.py browse "security"
python skills_sdk.py browse           # interactive/trending

# Preview what's in a repo
python skills_sdk.py install vercel-labs/agent-skills --list

# Install all skills from a repo → .gemini/skills/
python skills_sdk.py install vercel-labs/agent-skills

# Install one skill
python skills_sdk.py install obra/superpowers@requesting-code-review

# Install specific skills
python skills_sdk.py install obra/superpowers --skill systematic-debugging tdd-workflow
```

### Export catalog

```bash
python skills_sdk.py export                       # → skills-catalog.json
python skills_sdk.py export --output my-list.json
```

---

## load-skill.sh

A simpler shell script for copying the full skill library into a project in one step:

```bash
cd /path/to/your-project
bash /path/to/SkillLoader/load-skill.sh
```

Prompts you to choose an agent folder, then copies all 344 skills into that project.

---

## Categories

| Slug | Count | Description |
|---|---|---|
| `engineering` | 77 | Code review, TDD, git, CI/CD |
| `engineering-advanced` | 69 | Agents, AI patterns, multi-agent, context |
| `marketing` | 50 | SEO, ads, CRO, content strategy |
| `c-level` | 36 | CEO/CTO/CFO/CMO advisors, board |
| `command` | 29 | Slash-command utilities |
| `agent` | 23 | Persona-based agents |
| `ra-qm` | 15 | Quality, regulatory, compliance |
| `product` | 17 | Product management, strategy |
| `project-management` | 7 | Jira, Scrum, Confluence |
| `document` | 7 | docx, pdf, xlsx, pptx |
| `business-growth` | 6 | Sales, revenue ops |
| `finance` | 4 | Financial modeling, SaaS metrics |
| `workflow` | 4 | Planning, execution workflows |

---

## Python API

```python
from skills_sdk import list_skills, search_skills, get_skill, get_catalog

# List by category
for skill in list_skills("marketing"):
    print(skill["name"], "—", skill["description"][:60])

# Search
results = search_skills("docker")

# Look up one skill
skill = get_skill("systematic-debugging")
print(skill["path"])   # absolute path to SKILL.md on disk

# Full catalog
catalog = get_catalog()
print(catalog["total_skills"])
```

---

## Structure

```
SkillLoader/
  skills_sdk.py          # SDK + CLI
  load-skill.sh          # quick full-copy script
  .gemini/
    skills/              # 344 skill folders (single source of truth)
    skills-index.json    # category + description index
  claude-skills/         # git submodule — backs the skill symlinks
```
