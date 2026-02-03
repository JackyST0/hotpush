"""
数据库服务
支持 SQLite 和 MySQL 持久化存储
"""
import sqlite3
import os
import json
import bcrypt
from datetime import datetime
from typing import Set, Optional, Dict, Any, List
from contextlib import contextmanager
from urllib.parse import urlparse

from app.config import settings


class Database:
    """数据库管理，支持 SQLite 和 MySQL"""

    def __init__(self, db_url: str = None):
        if db_url is None:
            db_url = settings.database_url

        self.db_url = db_url
        self.db_type = self._parse_db_type(db_url)

        if self.db_type == "sqlite":
            self._init_sqlite(db_url)
        elif self.db_type == "mysql":
            self._init_mysql(db_url)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        self._init_db()

    def _parse_db_type(self, db_url: str) -> str:
        """解析数据库类型"""
        if db_url.startswith("sqlite"):
            return "sqlite"
        elif db_url.startswith("mysql"):
            return "mysql"
        else:
            return "unknown"

    def _init_sqlite(self, db_url: str):
        """初始化 SQLite 配置"""
        if db_url.startswith("sqlite:///"):
            self.db_path = db_url.replace("sqlite:///", "")
        else:
            self.db_path = "./data/hotpush.db"

        # 确保目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _init_mysql(self, db_url: str):
        """初始化 MySQL 配置"""
        # mysql://user:password@host:port/dbname
        parsed = urlparse(db_url)
        self.mysql_config = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") if parsed.path else "hotpush",
            "charset": "utf8mb4"
        }

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        elif self.db_type == "mysql":
            import pymysql
            conn = pymysql.connect(
                **self.mysql_config,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _execute(self, conn, sql: str, params: tuple = None):
        """执行 SQL，处理不同数据库的占位符差异"""
        cursor = conn.cursor()
        if self.db_type == "mysql":
            # SQLite 用 ?，MySQL 用 %s
            sql = sql.replace("?", "%s")
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor

    def _init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            if self.db_type == "sqlite":
                self._init_sqlite_tables(conn)
            elif self.db_type == "mysql":
                self._init_mysql_tables(conn)

    def _init_sqlite_tables(self, conn):
        """初始化 SQLite 表"""
        cursor = conn.cursor()

        # 已推送的热点记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pushed_items (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT,
                url TEXT,
                pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pushed_items_source
            ON pushed_items(source)
        """)

        # 抓取记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                item_count INTEGER DEFAULT 0
            )
        """)

        # 系统设置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 推送渠道配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_channels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 自定义数据源表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT DEFAULT '自定义',
                icon TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 推送规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                rule_type TEXT NOT NULL,
                rule_config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 推送历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                source TEXT,
                title TEXT,
                item_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_push_history_pushed_at
            ON push_history(pushed_at DESC)
        """)

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username
            ON users(username)
        """)

    def _init_mysql_tables(self, conn):
        """初始化 MySQL 表"""
        cursor = conn.cursor()

        # 已推送的热点记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pushed_items (
                id VARCHAR(255) PRIMARY KEY,
                source VARCHAR(100) NOT NULL,
                title TEXT,
                url TEXT,
                pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pushed_items_source (source)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 抓取记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(100) NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                item_count INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 系统设置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                `key` VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 推送渠道配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_channels (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                enabled TINYINT DEFAULT 1,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 自定义数据源表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_sources (
                id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                url TEXT NOT NULL,
                category VARCHAR(50) DEFAULT '自定义',
                icon TEXT,
                enabled TINYINT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 推送规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_rules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                enabled TINYINT DEFAULT 1,
                rule_type VARCHAR(50) NOT NULL,
                rule_config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 推送历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS push_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channel VARCHAR(50) NOT NULL,
                source VARCHAR(100),
                title TEXT,
                item_count INT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT,
                pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_push_history_pushed_at (pushed_at DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                INDEX idx_users_username (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

    def _row_to_dict(self, row) -> Optional[Dict]:
        """将数据库行转换为字典"""
        if row is None:
            return None
        if self.db_type == "sqlite":
            return dict(row)
        else:
            return row  # MySQL DictCursor 已经返回字典

    # ===== 已推送记录相关方法 =====

    def get_pushed_item_ids(self, source: str) -> Set[str]:
        """获取指定源已推送的 item ID 集合"""
        with self.get_connection() as conn:
            cursor = self._execute(conn,
                "SELECT id FROM pushed_items WHERE source = ?",
                (source,)
            )
            return {row["id"] if self.db_type == "mysql" else row["id"] for row in cursor.fetchall()}

    def mark_items_pushed(self, source: str, items: list):
        """标记条目为已推送"""
        if not items:
            return

        with self.get_connection() as conn:
            for item in items:
                if self.db_type == "sqlite":
                    self._execute(conn, """
                        INSERT OR REPLACE INTO pushed_items (id, source, title, url, pushed_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (item.id, source, item.title, item.url, datetime.now()))
                else:
                    self._execute(conn, """
                        INSERT INTO pushed_items (id, source, title, url, pushed_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE title=%s, url=%s, pushed_at=%s
                    """, (item.id, source, item.title, item.url, datetime.now(),
                          item.title, item.url, datetime.now()))

    def is_first_fetch(self, source: str) -> bool:
        """判断是否是该源的首次抓取"""
        with self.get_connection() as conn:
            cursor = self._execute(conn,
                "SELECT COUNT(*) as count FROM fetch_records WHERE source = ?",
                (source,)
            )
            row = cursor.fetchone()
            count = row["count"] if self.db_type == "mysql" else row["count"]
            return count == 0

    def record_fetch(self, source: str, item_count: int):
        """记录一次抓取"""
        with self.get_connection() as conn:
            self._execute(conn, """
                INSERT INTO fetch_records (source, fetched_at, item_count)
                VALUES (?, ?, ?)
            """, (source, datetime.now(), item_count))

    def cleanup_old_records(self, days: int = 7):
        """清理旧记录（保留最近 N 天）"""
        with self.get_connection() as conn:
            if self.db_type == "sqlite":
                self._execute(conn, """
                    DELETE FROM pushed_items WHERE pushed_at < datetime('now', ?)
                """, (f"-{days} days",))
                self._execute(conn, """
                    DELETE FROM fetch_records WHERE fetched_at < datetime('now', ?)
                """, (f"-{days} days",))
            else:
                self._execute(conn, """
                    DELETE FROM pushed_items WHERE pushed_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                """, (days,))
                self._execute(conn, """
                    DELETE FROM fetch_records WHERE fetched_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                """, (days,))

    # ===== 系统设置相关方法 =====

    def get_setting(self, key: str) -> Optional[str]:
        """获取系统设置"""
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = self._execute(conn, "SELECT value FROM settings WHERE `key` = ?", (key,))
            else:
                cursor = self._execute(conn, "SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return None

    def set_setting(self, key: str, value: str):
        """设置系统设置"""
        with self.get_connection() as conn:
            if self.db_type == "sqlite":
                self._execute(conn, """
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, value, datetime.now()))
            else:
                self._execute(conn, """
                    INSERT INTO settings (`key`, value, updated_at)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE value=%s, updated_at=%s
                """, (key, value, datetime.now(), value, datetime.now()))

    def get_all_settings(self) -> Dict[str, str]:
        """获取所有系统设置"""
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = self._execute(conn, "SELECT `key`, value FROM settings")
            else:
                cursor = self._execute(conn, "SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # ===== 推送渠道配置相关方法 =====

    def get_push_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """获取推送渠道配置"""
        with self.get_connection() as conn:
            cursor = self._execute(conn,
                "SELECT id, name, enabled, config FROM push_channels WHERE id = ?",
                (channel_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "enabled": bool(row["enabled"]),
                    "config": json.loads(row["config"]) if row["config"] else {}
                }
            return None

    def get_all_push_channels(self) -> List[Dict[str, Any]]:
        """获取所有推送渠道配置"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT id, name, enabled, config FROM push_channels")
            channels = []
            for row in cursor.fetchall():
                channels.append({
                    "id": row["id"],
                    "name": row["name"],
                    "enabled": bool(row["enabled"]),
                    "config": json.loads(row["config"]) if row["config"] else {}
                })
            return channels

    def save_push_channel(self, channel_id: str, name: str, enabled: bool, config: Dict[str, Any]):
        """保存推送渠道配置"""
        with self.get_connection() as conn:
            config_json = json.dumps(config)
            enabled_int = 1 if enabled else 0
            now = datetime.now()
            if self.db_type == "sqlite":
                self._execute(conn, """
                    INSERT OR REPLACE INTO push_channels (id, name, enabled, config, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (channel_id, name, enabled_int, config_json, now))
            else:
                self._execute(conn, """
                    INSERT INTO push_channels (id, name, enabled, config, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=%s, enabled=%s, config=%s, updated_at=%s
                """, (channel_id, name, enabled_int, config_json, now,
                      name, enabled_int, config_json, now))

    def delete_push_channel(self, channel_id: str):
        """删除推送渠道配置"""
        with self.get_connection() as conn:
            self._execute(conn, "DELETE FROM push_channels WHERE id = ?", (channel_id,))

    # ===== 自定义数据源相关方法 =====

    def get_custom_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """获取自定义数据源"""
        with self.get_connection() as conn:
            cursor = self._execute(conn,
                "SELECT * FROM custom_sources WHERE id = ?",
                (source_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "url": row["url"],
                    "category": row["category"],
                    "icon": row["icon"],
                    "enabled": bool(row["enabled"]),
                    "is_custom": True
                }
            return None

    def get_all_custom_sources(self) -> List[Dict[str, Any]]:
        """获取所有自定义数据源"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT * FROM custom_sources ORDER BY created_at DESC")
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    "id": row["id"],
                    "name": row["name"],
                    "url": row["url"],
                    "category": row["category"],
                    "icon": row["icon"],
                    "enabled": bool(row["enabled"]),
                    "is_custom": True
                })
            return sources

    def save_custom_source(self, source_id: str, name: str, url: str,
                          category: str = "自定义", icon: str = None, enabled: bool = True):
        """保存自定义数据源"""
        with self.get_connection() as conn:
            enabled_int = 1 if enabled else 0
            now = datetime.now()
            if self.db_type == "sqlite":
                self._execute(conn, """
                    INSERT OR REPLACE INTO custom_sources (id, name, url, category, icon, enabled, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (source_id, name, url, category, icon, enabled_int, now))
            else:
                self._execute(conn, """
                    INSERT INTO custom_sources (id, name, url, category, icon, enabled, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=%s, url=%s, category=%s, icon=%s, enabled=%s, updated_at=%s
                """, (source_id, name, url, category, icon, enabled_int, now,
                      name, url, category, icon, enabled_int, now))

    def delete_custom_source(self, source_id: str):
        """删除自定义数据源"""
        with self.get_connection() as conn:
            self._execute(conn, "DELETE FROM custom_sources WHERE id = ?", (source_id,))

    # ===== 推送规则相关方法 =====

    def get_push_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """获取推送规则"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT * FROM push_rules WHERE id = ?", (rule_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "enabled": bool(row["enabled"]),
                    "rule_type": row["rule_type"],
                    "rule_config": json.loads(row["rule_config"]) if row["rule_config"] else {}
                }
            return None

    def get_all_push_rules(self) -> List[Dict[str, Any]]:
        """获取所有推送规则"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT * FROM push_rules ORDER BY id")
            rules = []
            for row in cursor.fetchall():
                rules.append({
                    "id": row["id"],
                    "name": row["name"],
                    "enabled": bool(row["enabled"]),
                    "rule_type": row["rule_type"],
                    "rule_config": json.loads(row["rule_config"]) if row["rule_config"] else {}
                })
            return rules

    def get_enabled_push_rules(self) -> List[Dict[str, Any]]:
        """获取所有启用的推送规则"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT * FROM push_rules WHERE enabled = 1 ORDER BY id")
            rules = []
            for row in cursor.fetchall():
                rules.append({
                    "id": row["id"],
                    "name": row["name"],
                    "enabled": True,
                    "rule_type": row["rule_type"],
                    "rule_config": json.loads(row["rule_config"]) if row["rule_config"] else {}
                })
            return rules

    def save_push_rule(self, name: str, rule_type: str, rule_config: Dict[str, Any],
                      enabled: bool = True, rule_id: int = None) -> int:
        """保存推送规则，返回规则 ID"""
        with self.get_connection() as conn:
            config_json = json.dumps(rule_config)
            enabled_int = 1 if enabled else 0
            now = datetime.now()

            if rule_id:
                self._execute(conn, """
                    UPDATE push_rules SET name = ?, rule_type = ?, rule_config = ?, enabled = ?, updated_at = ?
                    WHERE id = ?
                """, (name, rule_type, config_json, enabled_int, now, rule_id))
                return rule_id
            else:
                cursor = self._execute(conn, """
                    INSERT INTO push_rules (name, rule_type, rule_config, enabled, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, rule_type, config_json, enabled_int, now))
                return cursor.lastrowid

    def delete_push_rule(self, rule_id: int):
        """删除推送规则"""
        with self.get_connection() as conn:
            self._execute(conn, "DELETE FROM push_rules WHERE id = ?", (rule_id,))

    # ===== 推送历史相关方法 =====

    def add_push_history(self, channel: str, source: str, title: str,
                        item_count: int, status: str = "success", error_message: str = None):
        """添加推送历史记录"""
        with self.get_connection() as conn:
            self._execute(conn, """
                INSERT INTO push_history (channel, source, title, item_count, status, error_message, pushed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (channel, source, title, item_count, status, error_message, datetime.now()))

    def get_push_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取推送历史"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, """
                SELECT * FROM push_history ORDER BY pushed_at DESC LIMIT ? OFFSET ?
            """, (limit, offset))
            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row["id"],
                    "channel": row["channel"],
                    "source": row["source"],
                    "title": row["title"],
                    "item_count": row["item_count"],
                    "status": row["status"],
                    "error_message": row["error_message"],
                    "pushed_at": str(row["pushed_at"]) if row["pushed_at"] else None
                })
            return history

    def get_push_history_count(self) -> int:
        """获取推送历史总数"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT COUNT(*) as count FROM push_history")
            row = cursor.fetchone()
            return row["count"]

    def cleanup_push_history(self, days: int = 30):
        """清理旧的推送历史"""
        with self.get_connection() as conn:
            if self.db_type == "sqlite":
                self._execute(conn, """
                    DELETE FROM push_history WHERE pushed_at < datetime('now', ?)
                """, (f"-{days} days",))
            else:
                self._execute(conn, """
                    DELETE FROM push_history WHERE pushed_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                """, (days,))

    # ===== 用户相关方法 =====

    def create_user(self, username: str, password: str, role: str = "user") -> int:
        """创建用户，返回用户 ID"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with self.get_connection() as conn:
            cursor = self._execute(conn, """
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, role, datetime.now()))
            return cursor.lastrowid

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """通过用户名获取用户"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "password_hash": row["password_hash"],
                    "role": row["role"],
                    "created_at": str(row["created_at"]) if row["created_at"] else None,
                    "last_login": str(row["last_login"]) if row["last_login"] else None
                }
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """通过 ID 获取用户"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "password_hash": row["password_hash"],
                    "role": row["role"],
                    "created_at": str(row["created_at"]) if row["created_at"] else None,
                    "last_login": str(row["last_login"]) if row["last_login"] else None
                }
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户"""
        with self.get_connection() as conn:
            cursor = self._execute(conn,
                "SELECT id, username, role, created_at, last_login FROM users ORDER BY created_at DESC")
            users = []
            for row in cursor.fetchall():
                users.append({
                    "id": row["id"],
                    "username": row["username"],
                    "role": row["role"],
                    "created_at": str(row["created_at"]) if row["created_at"] else None,
                    "last_login": str(row["last_login"]) if row["last_login"] else None
                })
            return users

    def update_user(self, user_id: int, username: str = None, password: str = None, role: str = None) -> bool:
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        new_username = username if username else user["username"]
        new_password_hash = user["password_hash"]
        if password:
            new_password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_role = role if role else user["role"]

        with self.get_connection() as conn:
            cursor = self._execute(conn, """
                UPDATE users SET username = ?, password_hash = ?, role = ?
                WHERE id = ?
            """, (new_username, new_password_hash, new_role, user_id))
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    def update_last_login(self, user_id: int):
        """更新用户最后登录时间"""
        with self.get_connection() as conn:
            self._execute(conn, """
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now(), user_id))

    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户密码，成功返回用户信息，失败返回 None"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            return user
        return None

    def get_admin_count(self) -> int:
        """获取管理员数量"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
            return cursor.fetchone()["count"]

    def get_user_count(self) -> int:
        """获取用户总数"""
        with self.get_connection() as conn:
            cursor = self._execute(conn, "SELECT COUNT(*) as count FROM users")
            return cursor.fetchone()["count"]

    def init_admin_user(self):
        """初始化管理员用户（首次启动时调用）"""
        # 检查是否已有用户
        if self.get_user_count() > 0:
            return

        # 检查是否配置了管理员密码
        if not settings.admin_password:
            return

        # 创建管理员用户
        self.create_user(
            username=settings.admin_username,
            password=settings.admin_password,
            role="admin"
        )


# 全局实例
db = Database()

# 初始化管理员用户
db.init_admin_user()
