"""Tests for link_vault.py"""
import json, os, sys, tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import link_vault as lv


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(lv, "DB_PATH", str(tmp_path / "test_vault.db"))
    yield tmp_path


def _save(url="https://example.com", title="Example", tags=None, collection=""):
    db = lv.get_db()
    from datetime import datetime
    db.execute("""
        INSERT OR IGNORE INTO links(url,title,description,tags_json,favicon_url,
            reading_time_min,is_read,is_starred,collection,saved_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)
    """, (url, title, "", json.dumps(tags or []), "", 0, 0, 0, collection,
          datetime.now().isoformat()))
    db.commit()
    return db.execute("SELECT id FROM links WHERE url=?", (url,)).fetchone()["id"]


def test_db_init(tmp_db):
    assert lv.get_db() is not None

def test_save_link(tmp_db):
    args = MagicMock(url="https://python.org", title="Python", description="",
                     tags="python,docs", collection="", reading_time=5)
    lv.cmd_save(args)
    db = lv.get_db()
    row = db.execute("SELECT * FROM links WHERE url='https://python.org'").fetchone()
    assert row is not None
    assert row["title"] == "Python"

def test_save_duplicate_no_error(tmp_db, capsys):
    args = MagicMock(url="https://dupe.com", title="Dupe", description="",
                     tags="", collection="", reading_time=0)
    lv.cmd_save(args)
    lv.cmd_save(args)   # Should warn, not crash
    out = capsys.readouterr()
    assert "already saved" in out.out

def test_read_marks_read(tmp_db):
    lid = _save()
    args = MagicMock(link_id=lid)
    lv.cmd_read(args)
    db  = lv.get_db()
    row = db.execute("SELECT is_read FROM links WHERE id=?", (lid,)).fetchone()
    assert row["is_read"] == 1

def test_star_toggles(tmp_db):
    lid = _save()
    args = MagicMock(link_id=lid)
    lv.cmd_star(args)
    db = lv.get_db()
    assert db.execute("SELECT is_starred FROM links WHERE id=?", (lid,)).fetchone()["is_starred"] == 1
    lv.cmd_star(args)
    assert db.execute("SELECT is_starred FROM links WHERE id=?", (lid,)).fetchone()["is_starred"] == 0

def test_search_fts(tmp_db):
    _save("https://rust-lang.org", "Rust Programming Language", ["rust"])
    db   = lv.get_db()
    rows = db.execute("""
        SELECT l.* FROM links l JOIN links_fts f ON l.id=f.rowid
        WHERE links_fts MATCH 'Rust' ORDER BY l.saved_at DESC
    """).fetchall()
    assert len(rows) >= 1

def test_by_tag(tmp_db, capsys):
    _save(tags=["python"])
    args = MagicMock(tag="python")
    lv.cmd_by_tag(args)
    out = capsys.readouterr().out
    assert "python" in out.lower() or "1 link" in out

def test_reading_queue(tmp_db, capsys):
    from datetime import datetime
    db = lv.get_db()
    db.execute("INSERT INTO links(url,title,description,tags_json,favicon_url,"
               "reading_time_min,is_read,is_starred,collection,saved_at) "
               "VALUES(?,?,?,?,?,?,?,?,?,?)",
               ("https://queue.com","Queue Item","","[]","",5,0,1,"",datetime.now().isoformat()))
    db.commit()
    args = MagicMock()
    lv.cmd_reading_queue(args)
    out = capsys.readouterr().out
    assert "Queue Item" in out or "queue" in out.lower()

def test_export_import_roundtrip(tmp_db, tmp_path):
    _save("https://export.com", "Export Test", ["export"])
    out_file = str(tmp_path / "export.json")
    args = MagicMock(output=out_file)
    lv.cmd_export_json(args)
    assert Path(out_file).exists()
    with open(out_file) as f: data = json.load(f)
    assert len(data) >= 1
    # Clear and re-import
    db = lv.get_db(); db.execute("DELETE FROM links"); db.commit()
    args2 = MagicMock(file=out_file)
    lv.cmd_import_json(args2)
    db = lv.get_db()
    assert db.execute("SELECT COUNT(*) FROM links").fetchone()[0] >= 1

def test_tag_stats(tmp_db, capsys):
    _save(tags=["python","api"])
    _save("https://b.com", tags=["python"])
    args = MagicMock()
    lv.cmd_tag_stats(args)
    out = capsys.readouterr().out
    assert "python" in out

def test_collection_create(tmp_db, capsys):
    args = MagicMock(name="my-list", description="Test", color="#FF0000")
    lv.cmd_collection_create(args)
    db  = lv.get_db()
    row = db.execute("SELECT * FROM collections WHERE name='my-list'").fetchone()
    assert row is not None
    assert row["color"] == "#FF0000"
