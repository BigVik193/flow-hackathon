#!/usr/bin/env python3
"""
Session Manager for Ultra-Fast Voice Agent

Handles intelligent session persistence, recovery, and user data management
across browser restarts and application sessions.
"""

import os
import json
import sqlite3
import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager


@dataclass
class BrowserSession:
    """Represents a persistent browser session"""
    session_id: str
    user_data_dir: str
    created_at: datetime
    last_accessed: datetime
    command_history: List[str]
    current_url: Optional[str] = None
    is_active: bool = True


class SessionManager:
    """Manages persistent browser sessions with automatic cleanup"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir()) / "voice_agent_sessions"
        self.base_dir.mkdir(exist_ok=True)
        
        self.db_path = self.base_dir / "sessions.db"
        self.sessions_dir = self.base_dir / "browser_sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for session tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_data_dir TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    command_history TEXT,
                    current_url TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            conn.commit()
    
    def create_session(self, session_id: Optional[str] = None) -> BrowserSession:
        """Create a new persistent browser session"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        
        # Create dedicated user data directory for this session
        user_data_dir = str(self.sessions_dir / session_id)
        os.makedirs(user_data_dir, exist_ok=True)
        
        session = BrowserSession(
            session_id=session_id,
            user_data_dir=user_data_dir,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            command_history=[],
        )
        
        self._save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Retrieve an existing session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ? AND is_active = 1",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return BrowserSession(
                session_id=row[0],
                user_data_dir=row[1],
                created_at=datetime.fromisoformat(row[2]),
                last_accessed=datetime.fromisoformat(row[3]),
                command_history=json.loads(row[4]) if row[4] else [],
                current_url=row[5],
                is_active=bool(row[6])
            )
    
    def update_session(self, session: BrowserSession):
        """Update session with new activity"""
        session.last_accessed = datetime.now()
        self._save_session(session)
    
    def add_command_to_session(self, session_id: str, command: str, url: Optional[str] = None):
        """Add a command to session history"""
        session = self.get_session(session_id)
        if session:
            session.command_history.append(command)
            if url:
                session.current_url = url
            session.last_accessed = datetime.now()
            
            # Keep only last 50 commands for performance
            if len(session.command_history) > 50:
                session.command_history = session.command_history[-50:]
            
            self._save_session(session)
    
    def _save_session(self, session: BrowserSession):
        """Save session to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_data_dir, created_at, last_accessed, command_history, current_url, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_data_dir,
                session.created_at.isoformat(),
                session.last_accessed.isoformat(),
                json.dumps(session.command_history),
                session.current_url,
                int(session.is_active)
            ))
            conn.commit()
    
    def list_active_sessions(self) -> List[BrowserSession]:
        """List all active sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE is_active = 1 ORDER BY last_accessed DESC"
            )
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append(BrowserSession(
                    session_id=row[0],
                    user_data_dir=row[1],
                    created_at=datetime.fromisoformat(row[2]),
                    last_accessed=datetime.fromisoformat(row[3]),
                    command_history=json.loads(row[4]) if row[4] else [],
                    current_url=row[5],
                    is_active=bool(row[6])
                ))
            
            return sessions
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age_hours"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get sessions to cleanup
            cursor = conn.execute(
                "SELECT session_id, user_data_dir FROM sessions WHERE last_accessed < ?",
                (cutoff_time.isoformat(),)
            )
            
            cleanup_count = 0
            for row in cursor.fetchall():
                session_id, user_data_dir = row
                
                # Remove user data directory
                try:
                    import shutil
                    if os.path.exists(user_data_dir):
                        shutil.rmtree(user_data_dir)
                except Exception as e:
                    print(f"Warning: Could not remove {user_data_dir}: {e}")
                
                cleanup_count += 1
            
            # Mark sessions as inactive
            conn.execute(
                "UPDATE sessions SET is_active = 0 WHERE last_accessed < ?",
                (cutoff_time.isoformat(),)
            )
            conn.commit()
            
            if cleanup_count > 0:
                print(f"🧹 Cleaned up {cleanup_count} old sessions")
    
    def get_or_create_default_session(self) -> BrowserSession:
        """Get the most recent session or create a new default one"""
        sessions = self.list_active_sessions()
        
        if sessions:
            # Return the most recently accessed session
            return sessions[0]
        else:
            # Create a new default session
            return self.create_session("default")
    
    def export_session_state(self, session_id: str) -> Optional[Dict]:
        """Export session state for backup or transfer"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Export browser storage state if available
        storage_state_file = Path(session.user_data_dir) / "storage_state.json"
        storage_state = None
        
        if storage_state_file.exists():
            try:
                with open(storage_state_file, 'r') as f:
                    storage_state = json.load(f)
            except Exception:
                pass
        
        return {
            "session": asdict(session),
            "storage_state": storage_state,
            "exported_at": datetime.now().isoformat()
        }
    
    def import_session_state(self, session_data: Dict) -> BrowserSession:
        """Import session state from backup"""
        session_info = session_data["session"]
        
        # Create session with imported data
        session = BrowserSession(
            session_id=session_info["session_id"],
            user_data_dir=session_info["user_data_dir"],
            created_at=datetime.fromisoformat(session_info["created_at"]),
            last_accessed=datetime.now(),  # Update to current time
            command_history=session_info["command_history"],
            current_url=session_info.get("current_url"),
            is_active=True
        )
        
        # Recreate user data directory
        os.makedirs(session.user_data_dir, exist_ok=True)
        
        # Restore storage state if available
        if "storage_state" in session_data and session_data["storage_state"]:
            storage_state_file = Path(session.user_data_dir) / "storage_state.json"
            try:
                with open(storage_state_file, 'w') as f:
                    json.dump(session_data["storage_state"], f)
            except Exception as e:
                print(f"Warning: Could not restore storage state: {e}")
        
        self._save_session(session)
        return session


# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def cleanup_sessions_periodically():
    """Background task to cleanup old sessions"""
    while True:
        try:
            manager = get_session_manager()
            manager.cleanup_old_sessions()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Session cleanup error: {e}")
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # Test the session manager
    manager = SessionManager()
    
    # Create test session
    session = manager.create_session("test_session")
    print(f"Created session: {session.session_id}")
    
    # Add some commands
    manager.add_command_to_session(session.session_id, "go to google.com", "https://google.com")
    manager.add_command_to_session(session.session_id, "search for python", "https://google.com/search?q=python")
    
    # Retrieve session
    retrieved = manager.get_session(session.session_id)
    print(f"Retrieved session with {len(retrieved.command_history)} commands")
    
    # List sessions
    sessions = manager.list_active_sessions()
    print(f"Active sessions: {len(sessions)}")
    
    # Export session state
    exported = manager.export_session_state(session.session_id)
    print(f"Exported session state: {len(str(exported))} characters")