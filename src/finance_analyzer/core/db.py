import sqlite3
import shutil
import os
from datetime import datetime

DB_NAME = "finance_analyzer.db"
BACKUP_DIR = "backups"
CURRENT_VERSION = 3

class Database:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._ensure_backup_dir()
        self._migrate()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _ensure_backup_dir(self):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

    def backup_db(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"finance_analyzer_{timestamp}.db")
        try:
            self.conn.commit()
            if os.path.exists(self.db_path):
                 params = sqlite3.connect(backup_path)
                 with params:
                     self.conn.backup(params)
                 params.close()
                 print(f"Backup created at {backup_path}")
        except Exception as e:
            print(f"Backup failed: {e}")

    def _migrate(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        
        cursor = self.conn.execute("SELECT value FROM meta WHERE key='schema_version'")
        row = cursor.fetchone()
        version = int(row['value']) if row else 0
        
        if version < CURRENT_VERSION:
            print(f"Migrating DB from version {version} to {CURRENT_VERSION}...")
            self.backup_db()
            
            if version < 1:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        amount REAL NOT NULL,
                        description TEXT NOT NULL,
                        source TEXT,
                        category TEXT,
                        txn_hash TEXT UNIQUE
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        category TEXT NOT NULL,
                        is_regex INTEGER DEFAULT 0
                    )
                """)
                version = 1

            if version < 2:
                try:
                    self.conn.execute("ALTER TABLE transactions ADD COLUMN clash_info TEXT")
                except Exception as e:
                    print(f"Migration error v2: {e}")
                version = 2

            if version < 3:
                try:
                    self.conn.execute("ALTER TABLE transactions ADD COLUMN is_manual INTEGER DEFAULT 0")
                except Exception as e:
                    print(f"Migration error v3: {e}")
                version = 3
            
            self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)", (str(version),))
            self.conn.commit()
            print("Migration complete.")

    def get_connection(self):
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
