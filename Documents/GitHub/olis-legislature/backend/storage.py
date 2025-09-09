"""
SQLite Storage Helper
Simple database operations for local persistence
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class Storage:
    """
    Simple SQLite storage for application data
    """
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize storage with database path"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        self.run_migrations()
    
    def init_database(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            # First create schema version table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize schema version if empty
            cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
            if cursor.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (1, "Initial schema")
                )
            
            conn.commit()
    
    def get_schema_version(self) -> int:
        """Get current schema version"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT MAX(version) FROM schema_version")
                row = cursor.fetchone()
                return row[0] if row[0] is not None else 0
        except sqlite3.OperationalError:
            # Schema version table doesn't exist yet
            return 0
    
    def run_migrations(self):
        """Run database migrations to latest version"""
        current_version = self.get_schema_version()
        
        # Define migrations - add new migrations here
        migrations = [
            # Example migration - uncomment and modify as needed:
            # {
            #     'version': 2,
            #     'description': 'Add index to events table',
            #     'sql': [
            #         'CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)',
            #         'CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)'
            #     ]
            # }
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for migration in migrations:
                if migration['version'] > current_version:
                    try:
                        print(f"Applying migration {migration['version']}: {migration['description']}")
                        
                        # Execute migration SQL
                        for sql in migration['sql']:
                            conn.execute(sql)
                        
                        # Record migration
                        conn.execute(
                            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                            (migration['version'], migration['description'])
                        )
                        
                        conn.commit()
                        print(f"Migration {migration['version']} applied successfully")
                        
                    except Exception as e:
                        conn.rollback()
                        print(f"Migration {migration['version']} failed: {e}")
                        raise
    
    def add_migration(self, version: int, description: str, sql_statements: List[str]):
        """
        Helper method to define a new migration programmatically
        This is mainly for testing or dynamic migrations
        """
        current_version = self.get_schema_version()
        
        if version <= current_version:
            return False  # Migration already applied or version too low
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                for sql in sql_statements:
                    conn.execute(sql)
                
                conn.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (version, description)
                )
                
                conn.commit()
                return True
                
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_migration_history(self) -> List[Dict]:
        """Get history of applied migrations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM schema_version ORDER BY version"
            )
            return [dict(row) for row in cursor]
    
    def log_event(self, event_type: str, data: Any = None) -> int:
        """Log an event with optional data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO events (event_type, data) VALUES (?, ?)",
                (event_type, json.dumps(data) if data else None)
            )
            return cursor.lastrowid
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent events, optionally filtered by type"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if event_type:
                cursor = conn.execute(
                    """SELECT * FROM events 
                       WHERE event_type = ? 
                       ORDER BY created_at DESC 
                       LIMIT ?""",
                    (event_type, limit)
                )
            else:
                cursor = conn.execute(
                    """SELECT * FROM events 
                       ORDER BY created_at DESC 
                       LIMIT ?""",
                    (limit,)
                )
            
            events = []
            for row in cursor:
                event = dict(row)
                if event['data']:
                    event['data'] = json.loads(event['data'])
                events.append(event)
            
            return events
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a state value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO state (key, value, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, json.dumps(value))
            )
            conn.commit()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM state WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return default
    
    def delete_state(self, key: str) -> bool:
        """Delete a state value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM state WHERE key = ?",
                (key,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def log(self, level: str, message: str) -> None:
        """Add a log entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO logs (level, message) VALUES (?, ?)",
                (level, message)
            )
            conn.commit()
    
    def get_logs(self, level: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent logs, optionally filtered by level"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if level:
                cursor = conn.execute(
                    """SELECT * FROM logs 
                       WHERE level = ? 
                       ORDER BY created_at DESC 
                       LIMIT ?""",
                    (level, limit)
                )
            else:
                cursor = conn.execute(
                    """SELECT * FROM logs 
                       ORDER BY created_at DESC 
                       LIMIT ?""",
                    (limit,)
                )
            
            return [dict(row) for row in cursor]
    
    def clear_old_data(self, days: int = 7) -> Dict[str, int]:
        """Clear data older than specified days"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        with sqlite3.connect(self.db_path) as conn:
            events_deleted = conn.execute(
                "DELETE FROM events WHERE created_at < datetime(?, 'unixepoch')",
                (cutoff,)
            ).rowcount
            
            logs_deleted = conn.execute(
                "DELETE FROM logs WHERE created_at < datetime(?, 'unixepoch')",
                (cutoff,)
            ).rowcount
            
            conn.commit()
            
        return {
            "events_deleted": events_deleted,
            "logs_deleted": logs_deleted
        }
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Count events
            cursor = conn.execute("SELECT COUNT(*) FROM events")
            stats['total_events'] = cursor.fetchone()[0]
            
            # Count logs
            cursor = conn.execute("SELECT COUNT(*) FROM logs")
            stats['total_logs'] = cursor.fetchone()[0]
            
            # Count state entries
            cursor = conn.execute("SELECT COUNT(*) FROM state")
            stats['state_entries'] = cursor.fetchone()[0]
            
            # Database size
            stats['db_size_kb'] = self.db_path.stat().st_size / 1024
            
            return stats


# Example usage
if __name__ == "__main__":
    # Test the storage
    storage = Storage()
    
    # Log an event
    event_id = storage.log_event("test_event", {"message": "Hello World"})
    print(f"Logged event with ID: {event_id}")
    
    # Set and get state
    storage.set_state("app_status", "running")
    status = storage.get_state("app_status")
    print(f"App status: {status}")
    
    # Get stats
    stats = storage.get_stats()
    print(f"Database stats: {stats}")
