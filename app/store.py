# -*- coding: utf-8 -*-
"""
로컬 저장 — 재료 용량 범위와 실행 이력.

SQLite 파일 하나(remi.db)에 담는다. 로컬 전용이라 이걸로 충분하고,
나중에 배포로 갈 때 이 모듈만 갈아끼우면 되도록 나머지 코드는
여기 함수 이름에만 의존한다.

용량 범위가 왜 DB 에 있나
-------------------------
온톨로지의 limitations 는 자유 서술이라 기계가 못 읽는다(스펙 G5). 그래서
"이 재료는 몇 %까지" 를 사람이 넣어줘야 하는데, 그 값은 온톨로지에 속한
보편 지식이 아니라 **이 랩의 작업 조건**이다. 그래서 온톨로지가 아니라
여기에 둔다. 온톨로지는 깨끗하게 유지되고, 범위는 제품마다 다를 수 있다.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(_HERE), "data", "remi.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bounds (
    profile     TEXT NOT NULL,
    ingredient  TEXT NOT NULL,
    lo          REAL NOT NULL,
    hi          REAL NOT NULL,
    note        TEXT,
    updated     TEXT NOT NULL,
    PRIMARY KEY (profile, ingredient)
);
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created     TEXT NOT NULL,
    profile     TEXT NOT NULL,
    data_file   TEXT,
    n_samples   INTEGER,
    y_terms     TEXT,
    target      TEXT,
    proposal    TEXT,
    note        TEXT
);
"""


def _conn(path=None):
    p = path or DB_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True)
    c = sqlite3.connect(p)
    c.executescript(_SCHEMA)
    return c


# ------------------------------------------------------------------ 용량 범위
def get_bounds(profile, path=None):
    """{ING.*: (lo, hi)} — adapter/propose 가 그대로 받는 형태."""
    with _conn(path) as c:
        rows = c.execute(
            "SELECT ingredient, lo, hi FROM bounds WHERE profile=?", (profile,)).fetchall()
    return {r[0]: (r[1], r[2]) for r in rows}


def get_bounds_detail(profile, path=None):
    with _conn(path) as c:
        return c.execute(
            "SELECT ingredient, lo, hi, note, updated FROM bounds "
            "WHERE profile=? ORDER BY ingredient", (profile,)).fetchall()


def set_bound(profile, ingredient, lo, hi, note="", path=None):
    if hi <= lo:
        raise ValueError(f"상한({hi})이 하한({lo})보다 커야 합니다.")
    if lo < 0:
        raise ValueError("하한은 0 이상이어야 합니다.")
    with _conn(path) as c:
        c.execute(
            "INSERT INTO bounds (profile, ingredient, lo, hi, note, updated) "
            "VALUES (?,?,?,?,?,?) ON CONFLICT(profile, ingredient) DO UPDATE SET "
            "lo=excluded.lo, hi=excluded.hi, note=excluded.note, updated=excluded.updated",
            (profile, ingredient, float(lo), float(hi), note,
             datetime.now().isoformat(timespec="seconds")))


def delete_bound(profile, ingredient, path=None):
    with _conn(path) as c:
        c.execute("DELETE FROM bounds WHERE profile=? AND ingredient=?",
                  (profile, ingredient))


def import_bounds(profile, mapping, note="", path=None):
    """{ING.*: (lo, hi)} 를 한꺼번에. 데모 팔레트를 씨앗으로 넣을 때 쓴다."""
    n = 0
    for g, (lo, hi) in mapping.items():
        set_bound(profile, g, lo, hi, note, path)
        n += 1
    return n


# ------------------------------------------------------------------ 실행 이력
def log_run(profile, data_file, n_samples, y_terms, target=None,
            proposal=None, note="", path=None):
    with _conn(path) as c:
        cur = c.execute(
            "INSERT INTO runs (created, profile, data_file, n_samples, y_terms, "
            "target, proposal, note) VALUES (?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), profile, data_file,
             int(n_samples), json.dumps(y_terms, ensure_ascii=False),
             json.dumps(target, ensure_ascii=False) if target else None,
             json.dumps(proposal, ensure_ascii=False) if proposal else None, note))
        return cur.lastrowid


def recent_runs(limit=20, path=None):
    with _conn(path) as c:
        return c.execute(
            "SELECT id, created, profile, n_samples, target, proposal FROM runs "
            "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
