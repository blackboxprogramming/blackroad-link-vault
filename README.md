<!-- BlackRoad SEO Enhanced -->

# ulackroad link vault

> Part of **[BlackRoad OS](https://blackroad.io)** — Sovereign Computing for Everyone

[![BlackRoad OS](https://img.shields.io/badge/BlackRoad-OS-ff1d6c?style=for-the-badge)](https://blackroad.io)
[![BlackRoad-Forge](https://img.shields.io/badge/Org-BlackRoad-Forge-2979ff?style=for-the-badge)](https://github.com/BlackRoad-Forge)

**ulackroad link vault** is part of the **BlackRoad OS** ecosystem — a sovereign, distributed operating system built on edge computing, local AI, and mesh networking by **BlackRoad OS, Inc.**

### BlackRoad Ecosystem
| Org | Focus |
|---|---|
| [BlackRoad OS](https://github.com/BlackRoad-OS) | Core platform |
| [BlackRoad OS, Inc.](https://github.com/BlackRoad-OS-Inc) | Corporate |
| [BlackRoad AI](https://github.com/BlackRoad-AI) | AI/ML |
| [BlackRoad Hardware](https://github.com/BlackRoad-Hardware) | Edge hardware |
| [BlackRoad Security](https://github.com/BlackRoad-Security) | Cybersecurity |
| [BlackRoad Quantum](https://github.com/BlackRoad-Quantum) | Quantum computing |
| [BlackRoad Agents](https://github.com/BlackRoad-Agents) | AI agents |
| [BlackRoad Network](https://github.com/BlackRoad-Network) | Mesh networking |

**Website**: [blackroad.io](https://blackroad.io) | **Chat**: [chat.blackroad.io](https://chat.blackroad.io) | **Search**: [search.blackroad.io](https://search.blackroad.io)

---


Personal bookmarks and link management with tags, collections, FTS5 search, and reading queue.

## Usage

```bash
# Save a link
python link_vault.py save "https://docs.python.org" \
  --title "Python Docs" --tags "python,docs,reference" \
  --collection "dev-resources" --reading-time 10

# Search
python link_vault.py search "python"

# By tag
python link_vault.py by-tag python

# Mark as read
python link_vault.py read 1

# Star / unstar
python link_vault.py star 1

# Reading queue (starred + unread)
python link_vault.py reading-queue

# Tag stats
python link_vault.py tag-stats

# List recent
python link_vault.py list --limit 20

# Collections
python link_vault.py collection-create "dev-resources" --color "#2979FF"
python link_vault.py collections

# Export / import
python link_vault.py export --output my_links.json
python link_vault.py import my_links.json
```

## Storage

SQLite at `~/.blackroad-personal/link_vault.db` with FTS5.

## License

Proprietary — BlackRoad OS, Inc.
