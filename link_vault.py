#!/usr/bin/env python3
"""BlackRoad Link Vault – personal bookmarks with tags, collections, and FTS5 search."""

import argparse, json, os, sqlite3, sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

GREEN  = "\033[0;32m"; RED    = "\033[0;31m"; YELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"; BOLD   = "\033[1m";    NC     = "\033[0m"
def ok(m):   print(f"{GREEN}✓{NC} {m}")
def err(m):  print(f"{RED}✗{NC} {m}", file=sys.stderr)
def info(m): print(f"{CYAN}ℹ{NC} {m}")
def warn(m): print(f"{YELLOW}⚠{NC} {m}")

DB_PATH = os.path.expanduser("~/.blackroad-personal/link_vault.db")

@dataclass
class Link:
    id: int
    url: str
    title: str
    description: str
    tags: List[str]
    favicon_url: str
    reading_time_min: int
    is_read: bool
    is_starred: bool
    collection: str
    saved_at: str

@dataclass
class Collection:
    name: str
    description: str
    color: str

def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS links (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            url              TEXT NOT NULL UNIQUE,
            title            TEXT NOT NULL DEFAULT '',
            description      TEXT NOT NULL DEFAULT '',
            tags_json        TEXT NOT NULL DEFAULT '[]',
            favicon_url      TEXT NOT NULL DEFAULT '',
            reading_time_min INTEGER NOT NULL DEFAULT 0,
            is_read          INTEGER NOT NULL DEFAULT 0,
            is_starred       INTEGER NOT NULL DEFAULT 0,
            collection       TEXT NOT NULL DEFAULT '',
            saved_at         TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS collections (
            name        TEXT PRIMARY KEY,
            description TEXT NOT NULL DEFAULT '',
            color       TEXT NOT NULL DEFAULT '#2979FF'
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS links_fts USING fts5(
            title, description, tags_json, url,
            content='links', content_rowid='id'
        );
        CREATE TRIGGER IF NOT EXISTS links_ai AFTER INSERT ON links BEGIN
            INSERT INTO links_fts(rowid,title,description,tags_json,url)
            VALUES(new.id,new.title,new.description,new.tags_json,new.url);
        END;
        CREATE TRIGGER IF NOT EXISTS links_ad AFTER DELETE ON links BEGIN
            INSERT INTO links_fts(links_fts,rowid,title,description,tags_json,url)
            VALUES('delete',old.id,old.title,old.description,old.tags_json,old.url);
        END;
        CREATE TRIGGER IF NOT EXISTS links_au AFTER UPDATE ON links BEGIN
            INSERT INTO links_fts(links_fts,rowid,title,description,tags_json,url)
            VALUES('delete',old.id,old.title,old.description,old.tags_json,old.url);
            INSERT INTO links_fts(rowid,title,description,tags_json,url)
            VALUES(new.id,new.title,new.description,new.tags_json,new.url);
        END;
    """)
    conn.commit()
    return conn

def row_to_link(row) -> Link:
    d = dict(row)
    return Link(id=d["id"], url=d["url"], title=d["title"],
                description=d["description"], tags=json.loads(d["tags_json"]),
                favicon_url=d["favicon_url"], reading_time_min=d["reading_time_min"],
                is_read=bool(d["is_read"]), is_starred=bool(d["is_starred"]),
                collection=d["collection"], saved_at=d["saved_at"])

def print_link(link: Link, short=False):
    star = "⭐" if link.is_starred else "  "
    read = f"{GREEN}✓{NC}" if link.is_read else f"{YELLOW}○{NC}"
    tags = " ".join(f"#{t}" for t in link.tags) if link.tags else ""
    print(f"{star} [{link.id:>4}] {read} {CYAN}{link.title or link.url}{NC}")
    if not short:
        print(f"         {link.url}")
        if link.description: print(f"         {link.description}")
        if tags: print(f"         {tags}")
        if link.reading_time_min: print(f"         ⏱ {link.reading_time_min} min read")
        if link.collection: print(f"         📁 {link.collection}")

def cmd_save(args):
    db   = get_db()
    tags = [t.strip().lstrip("#") for t in args.tags.split(",")] if args.tags else []
    try:
        db.execute("""
            INSERT INTO links (url,title,description,tags_json,favicon_url,
                reading_time_min,collection,saved_at)
            VALUES(?,?,?,?,?,?,?,?)
        """, (args.url, args.title or "", args.description or "",
              json.dumps(tags), "", args.reading_time or 0,
              args.collection or "", datetime.now().isoformat()))
        db.commit()
        ok(f"Saved: {args.url}")
    except sqlite3.IntegrityError:
        warn(f"URL already saved: {args.url}")

def cmd_read(args):
    db = get_db()
    db.execute("UPDATE links SET is_read=1 WHERE id=?", (args.link_id,))
    db.commit()
    row = db.execute("SELECT * FROM links WHERE id=?", (args.link_id,)).fetchone()
    if row:
        ok(f"Marked as read: {row['title'] or row['url']}")

def cmd_star(args):
    db = get_db()
    row = db.execute("SELECT is_starred FROM links WHERE id=?", (args.link_id,)).fetchone()
    if not row:
        err(f"Link #{args.link_id} not found"); return
    new_state = 0 if row["is_starred"] else 1
    db.execute("UPDATE links SET is_starred=? WHERE id=?", (new_state, args.link_id))
    db.commit()
    ok(("Starred" if new_state else "Unstarred") + f" link #{args.link_id}")

def cmd_search(args):
    db   = get_db()
    rows = db.execute("""
        SELECT l.* FROM links l JOIN links_fts f ON l.id=f.rowid
        WHERE links_fts MATCH ? ORDER BY l.saved_at DESC LIMIT 20
    """, (args.query,)).fetchall()
    if not rows:
        info(f"No results for \"{args.query}\""); return
    info(f"{len(rows)} result(s)")
    for row in rows: print_link(row_to_link(row), short=True)

def cmd_by_tag(args):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM links WHERE tags_json LIKE ? ORDER BY saved_at DESC",
        (f'%"{args.tag}"%',)
    ).fetchall()
    if not rows:
        warn(f"No links tagged #{args.tag}"); return
    info(f"{len(rows)} link(s) tagged #{args.tag}")
    for row in rows: print_link(row_to_link(row), short=True)

def cmd_by_collection(args):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM links WHERE collection=? ORDER BY saved_at DESC", (args.name,)
    ).fetchall()
    if not rows:
        warn(f"Collection \"{args.name}\" is empty"); return
    for row in rows: print_link(row_to_link(row), short=True)

def cmd_reading_queue(args):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM links WHERE is_read=0 AND is_starred=1 ORDER BY saved_at"
    ).fetchall()
    if not rows:
        info("Reading queue is empty"); return
    print(f"\n{BOLD}Reading queue ({len(rows)} links):{NC}")
    for row in rows: print_link(row_to_link(row))

def cmd_tag_stats(args):
    db   = get_db()
    rows = db.execute("SELECT tags_json FROM links").fetchall()
    freq: dict = {}
    for row in rows:
        for t in json.loads(row["tags_json"]):
            freq[t] = freq.get(t, 0) + 1
    if not freq:
        warn("No tags yet"); return
    print(f"\n{BOLD}Tag statistics:{NC}")
    for tag, cnt in sorted(freq.items(), key=lambda x: -x[1])[:20]:
        bar = "█" * cnt
        print(f"  #{tag:<25} {bar} {cnt}")

def cmd_export_json(args):
    db   = get_db()
    rows = db.execute("SELECT * FROM links ORDER BY saved_at DESC").fetchall()
    data = []
    for row in rows:
        d = dict(row)
        d["tags"] = json.loads(d.pop("tags_json"))
        data.append(d)
    fname = args.output or "link_vault_export.json"
    with open(fname, "w") as f: json.dump(data, f, indent=2)
    ok(f"Exported {len(data)} links to {fname}")

def cmd_import_json(args):
    with open(args.file) as f: data = json.load(f)
    db = get_db()
    imported = 0
    for item in data:
        try:
            tags = item.get("tags", [])
            db.execute("""
                INSERT OR IGNORE INTO links
                  (url,title,description,tags_json,favicon_url,reading_time_min,
                   is_read,is_starred,collection,saved_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """, (item["url"], item.get("title",""), item.get("description",""),
                  json.dumps(tags), item.get("favicon_url",""),
                  item.get("reading_time_min",0), item.get("is_read",0),
                  item.get("is_starred",0), item.get("collection",""),
                  item.get("saved_at", datetime.now().isoformat())))
            imported += 1
        except Exception: pass
    db.commit()
    ok(f"Imported {imported}/{len(data)} links")

def cmd_list(args):
    db   = get_db()
    limit = args.limit or 20
    rows = db.execute("SELECT * FROM links ORDER BY saved_at DESC LIMIT ?", (limit,)).fetchall()
    if not rows:
        warn("No links saved"); return
    for row in rows: print_link(row_to_link(row), short=True)

def cmd_collection_create(args):
    db = get_db()
    db.execute("INSERT OR REPLACE INTO collections(name,description,color) VALUES(?,?,?)",
               (args.name, args.description or "", args.color or "#2979FF"))
    db.commit()
    ok(f"Collection \"{args.name}\" created")

def cmd_collections_list(args):
    db = get_db()
    rows = db.execute("SELECT c.*, COUNT(l.id) as cnt FROM collections c "
                      "LEFT JOIN links l ON l.collection=c.name GROUP BY c.name").fetchall()
    if not rows:
        warn("No collections"); return
    for r in rows:
        print(f"  {CYAN}{r['name']}{NC}  ({r['cnt']} links)  {r['description']}")

def main():
    parser = argparse.ArgumentParser(prog="br-vault", description="BlackRoad Link Vault")
    sub    = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("save"); p.add_argument("url")
    p.add_argument("--title","--t",dest="title",default="")
    p.add_argument("--description","--d",dest="description",default="")
    p.add_argument("--tags",default="")
    p.add_argument("--collection",default="")
    p.add_argument("--reading-time",dest="reading_time",type=int,default=0)
    p.set_defaults(func=cmd_save)

    p = sub.add_parser("read");   p.add_argument("link_id",type=int); p.set_defaults(func=cmd_read)
    p = sub.add_parser("star");   p.add_argument("link_id",type=int); p.set_defaults(func=cmd_star)
    p = sub.add_parser("search"); p.add_argument("query");             p.set_defaults(func=cmd_search)
    p = sub.add_parser("by-tag"); p.add_argument("tag");               p.set_defaults(func=cmd_by_tag)
    p = sub.add_parser("by-collection"); p.add_argument("name");       p.set_defaults(func=cmd_by_collection)
    sub.add_parser("reading-queue").set_defaults(func=cmd_reading_queue)
    sub.add_parser("tag-stats").set_defaults(func=cmd_tag_stats)

    p = sub.add_parser("export"); p.add_argument("--output",default=None); p.set_defaults(func=cmd_export_json)
    p = sub.add_parser("import"); p.add_argument("file");                   p.set_defaults(func=cmd_import_json)
    p = sub.add_parser("list");   p.add_argument("--limit",type=int,default=20); p.set_defaults(func=cmd_list)

    p = sub.add_parser("collection-create")
    p.add_argument("name"); p.add_argument("--description",default=""); p.add_argument("--color",default="#2979FF")
    p.set_defaults(func=cmd_collection_create)
    sub.add_parser("collections").set_defaults(func=cmd_collections_list)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
