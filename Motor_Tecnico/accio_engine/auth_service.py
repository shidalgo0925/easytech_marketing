#!/usr/bin/env python3
"""Autenticación, usuarios globales y acceso por tenant."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from werkzeug.security import check_password_hash

from Motor_Tecnico.accio_engine.tenant import list_tenants

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUTH_DB = BASE_DIR / "Marketing" / "tenants" / ".secrets" / "auth.db"

ROLE_ALIASES = {
    "admin": "tenant_admin",
    "operator": "marketing_operator",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                global_role TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_tenants (
                user_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                role TEXT NOT NULL,
                PRIMARY KEY (user_id, tenant_id)
            )
            """
        )
        conn.commit()


def _normalize_role(role: str) -> str:
    role = (role or "viewer").strip()
    return ROLE_ALIASES.get(role, role)


def migrate_from_tenant_json() -> int:
    """Importa users.json de cada tenant a auth.db (una sola vez por email)."""
    _ensure_db()
    imported = 0
    with sqlite3.connect(AUTH_DB) as conn:
        for tenant in list_tenants():
            path = tenant.root / "users.json"
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for u in data.get("users", []):
                email = (u.get("email") or "").strip().lower()
                if not email:
                    email = f"{u.get('id', 'user')}@{tenant.tenant_id}.local"
                ph = u.get("password_hash")
                if not ph:
                    continue
                existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                if existing:
                    user_id = existing[0]
                else:
                    desired_id = u.get("id") or str(uuid.uuid4())[:12]
                    id_taken = conn.execute("SELECT 1 FROM users WHERE id = ?", (desired_id,)).fetchone()
                    user_id = desired_id if not id_taken else str(uuid.uuid4())[:12]
                    now = _utc_now()
                    conn.execute(
                        """
                        INSERT INTO users (id, email, name, password_hash, global_role, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                        """,
                        (
                            user_id,
                            email,
                            u.get("name") or u.get("id", "Usuario"),
                            ph,
                            1 if u.get("active", True) else 0,
                            now,
                            now,
                        ),
                    )
                    imported += 1
                role = _normalize_role(u.get("role", "tenant_admin"))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_tenants (user_id, tenant_id, role)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, tenant.tenant_id, role),
                )
        conn.commit()
    return imported


def authenticate_user(login: str, password: str) -> dict[str, Any] | None:
    """Valida credenciales sin empresa; devuelve empresas a las que tiene acceso."""
    _ensure_db()
    login = (login or "").strip().lower()
    if not login or not password:
        return None
    with sqlite3.connect(AUTH_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE (email = ? OR id = ?) AND is_active = 1",
            (login, login),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return None
        user_id = row["id"]
        global_role = row["global_role"]
        companies = allowed_tenants(user_id, global_role)
        if global_role != "super_admin" and not companies:
            return None
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_utc_now(), user_id))
        conn.commit()
    return {
        "user_id": user_id,
        "email": row["email"],
        "name": row["name"],
        "global_role": global_role,
        "companies": companies,
    }


def authenticate(login: str, password: str, tenant_id: str) -> dict[str, Any] | None:
    _ensure_db()
    login = (login or "").strip().lower()
    if not login or not password:
        return None
    with sqlite3.connect(AUTH_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE (email = ? OR id = ?) AND is_active = 1",
            (login, login),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return None
        user_id = row["id"]
        global_role = row["global_role"]
        if global_role == "super_admin":
            role = "super_admin"
        else:
            ut = conn.execute(
                "SELECT role FROM user_tenants WHERE user_id = ? AND tenant_id = ?",
                (user_id, tenant_id),
            ).fetchone()
            if not ut:
                return None
            role = _normalize_role(ut["role"])
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_utc_now(), user_id))
        conn.commit()
    return {
        "user_id": user_id,
        "email": row["email"],
        "name": row["name"],
        "role": role,
        "global_role": global_role,
    }


def can_access_tenant(user_id: str, tenant_id: str, global_role: str | None = None) -> bool:
    if global_role == "super_admin" or user_id == "api_key":
        return True
    _ensure_db()
    with sqlite3.connect(AUTH_DB) as conn:
        row = conn.execute(
            "SELECT 1 FROM user_tenants WHERE user_id = ? AND tenant_id = ?",
            (user_id, tenant_id),
        ).fetchone()
    return row is not None


def allowed_tenants(user_id: str, global_role: str | None = None) -> list[str]:
    if global_role == "super_admin" or user_id == "api_key":
        return [t.tenant_id for t in list_tenants()]
    _ensure_db()
    with sqlite3.connect(AUTH_DB) as conn:
        rows = conn.execute(
            "SELECT tenant_id FROM user_tenants WHERE user_id = ? ORDER BY tenant_id",
            (user_id,),
        ).fetchall()
    return [r[0] for r in rows]


def role_permissions(role: str) -> set[str]:
    role = _normalize_role(role)
    if role == "super_admin":
        return {"read", "publish", "config", "admin"}
    if role == "tenant_admin":
        return {"read", "publish", "config", "admin"}
    if role == "marketing_operator":
        return {"read", "publish"}
    if role == "viewer":
        return {"read"}
    return {"read"}


def get_tenant_role(user_id: str, tenant_id: str, global_role: str | None = None) -> str | None:
    if global_role == "super_admin" or user_id == "api_key":
        return "super_admin" if user_id != "api_key" else "tenant_admin"
    _ensure_db()
    with sqlite3.connect(AUTH_DB) as conn:
        row = conn.execute(
            "SELECT role FROM user_tenants WHERE user_id = ? AND tenant_id = ?",
            (user_id, tenant_id),
        ).fetchone()
    if not row:
        return None
    return _normalize_role(row[0])


def upsert_user(
    email: str,
    password: str,
    *,
    tenant_id: str,
    role: str = "tenant_admin",
    name: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Crea o actualiza usuario global + asignación de tenant."""
    from werkzeug.security import generate_password_hash

    _ensure_db()
    email = email.strip().lower()
    name = name or email.split("@")[0]
    role = _normalize_role(role)
    password_hash = generate_password_hash(password)
    now = _utc_now()
    with sqlite3.connect(AUTH_DB) as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            uid = existing[0]
            conn.execute(
                "UPDATE users SET password_hash=?, name=?, updated_at=?, is_active=1 WHERE id=?",
                (password_hash, name, now, uid),
            )
        else:
            uid = user_id or email.split("@")[0]
            if conn.execute("SELECT 1 FROM users WHERE id = ?", (uid,)).fetchone():
                uid = str(uuid.uuid4())[:12]
            conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, global_role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?)
                """,
                (uid, email, name, password_hash, now, now),
            )
        conn.execute(
            "INSERT OR REPLACE INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
            (uid, tenant_id, role),
        )
        conn.commit()
    return {"user_id": uid, "email": email, "name": name, "role": role, "tenant_id": tenant_id}


def has_permission(role: str, permission: str) -> bool:
    return permission in role_permissions(role)


def assign_user_tenant(user_id: str, tenant_id: str, role: str = "tenant_admin") -> None:
    """Vincula un usuario existente a un tenant (p. ej. tras crear empresa)."""
    if not user_id or not tenant_id:
        return
    _ensure_db()
    role = _normalize_role(role)
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
            (user_id, tenant_id.strip().lower(), role),
        )
        conn.commit()


def list_tenant_users(tenant_id: str) -> list[dict[str, Any]]:
    """Usuarios asignados a una empresa."""
    _ensure_db()
    tid = tenant_id.strip().lower()
    with sqlite3.connect(AUTH_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT u.id, u.email, u.name, u.is_active, ut.role
            FROM users u
            JOIN user_tenants ut ON u.id = ut.user_id
            WHERE ut.tenant_id = ?
            ORDER BY u.email COLLATE NOCASE
            """,
            (tid,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "email": row["email"],
            "name": row["name"],
            "role": _normalize_role(row["role"]),
            "active": bool(row["is_active"]),
        }
        for row in rows
    ]


def remove_user_from_tenant(user_id: str, tenant_id: str) -> None:
    if not user_id or not tenant_id:
        return
    _ensure_db()
    tid = tenant_id.strip().lower()
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute(
            "DELETE FROM user_tenants WHERE user_id = ? AND tenant_id = ?",
            (user_id, tid),
        )
        remaining = conn.execute(
            "SELECT COUNT(*) FROM user_tenants WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        if remaining == 0:
            conn.execute("UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?", (_utc_now(), user_id))
        conn.commit()


def save_tenant_user(
    tenant_id: str,
    *,
    user_id: str,
    email: str,
    name: str,
    role: str,
    active: bool = True,
    password: str | None = None,
) -> dict[str, Any]:
    """Crea o actualiza usuario de una empresa. Password opcional si ya existe."""
    from werkzeug.security import generate_password_hash

    _ensure_db()
    tid = tenant_id.strip().lower()
    uid = (user_id or "").strip()
    email = (email or "").strip().lower()
    name = (name or email.split("@")[0] or uid).strip()
    role = _normalize_role(role)
    if not uid or not email:
        raise ValueError("ID y email son obligatorios")
    now = _utc_now()
    with sqlite3.connect(AUTH_DB) as conn:
        by_id = conn.execute("SELECT id, email FROM users WHERE id = ?", (uid,)).fetchone()
        by_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if by_email and by_email[0] != uid:
            raise ValueError(f"El email {email} ya pertenece a otro usuario")
        if by_id and by_id[1].lower() != email:
            other = conn.execute("SELECT 1 FROM users WHERE email = ? AND id != ?", (email, uid)).fetchone()
            if other:
                raise ValueError(f"El email {email} ya está en uso")
        if by_id or by_email:
            real_id = by_id[0] if by_id else by_email[0]
            fields = ["name = ?", "email = ?", "is_active = ?", "updated_at = ?"]
            values: list[Any] = [name, email, 1 if active else 0, now]
            if password:
                fields.insert(0, "password_hash = ?")
                values.insert(0, generate_password_hash(password))
            values.append(real_id)
            conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
            uid = real_id
        else:
            if not password:
                raise ValueError(f"Contraseña obligatoria para usuario nuevo: {uid}")
            conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, global_role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (uid, email, name, generate_password_hash(password), 1 if active else 0, now, now),
            )
        conn.execute(
            "INSERT OR REPLACE INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
            (uid, tid, role),
        )
        conn.commit()
    return {"id": uid, "email": email, "name": name, "role": role, "active": active}


def sync_tenant_users(tenant_id: str, users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sincroniza lista completa de usuarios de una empresa (alta, edición, baja)."""
    tid = tenant_id.strip().lower()
    current = {u["id"]: u for u in list_tenant_users(tid)}
    keep_ids: set[str] = set()
    for row in users:
        uid = (row.get("id") or "").strip()
        if not uid:
            continue
        keep_ids.add(uid)
        save_tenant_user(
            tid,
            user_id=uid,
            email=row.get("email") or "",
            name=row.get("name") or uid,
            role=row.get("role") or "viewer",
            active=bool(row.get("active", True)),
            password=(row.get("password") or "").strip() or None,
        )
    for uid in set(current) - keep_ids:
        remove_user_from_tenant(uid, tid)
    return list_tenant_users(tid)
