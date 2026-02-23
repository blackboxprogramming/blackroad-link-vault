# blackroad-link-vault

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
