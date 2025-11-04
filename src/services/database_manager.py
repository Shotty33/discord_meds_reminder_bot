# src/services/database_manager.py
import os, sqlite3, threading, logging
from pathlib import Path
from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config: ConfigLoader):
        self._path = config.get_sqlite_path()
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()

        with self._conn:
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA journal_mode = WAL;")

        self._apply_schema()

        logger.info("SQLite ready at %s", self._path)

    def _apply_schema(self) -> None:
        # 1) explicit env override
        schema_env = os.getenv("SCHEMA_PATH")
        tried = []

        if schema_env:
            p = Path(schema_env)
            if not p.is_absolute():
                p = Path.cwd() / p
            tried.append(str(p))
            if p.is_file():
                ddl = p.read_text(encoding="utf-8")
                with self._conn:
                    self._conn.executescript(ddl)
                logger.info("✅ Loaded schema from %s", p)
                return

        # 2) project_root/database/schema.sql
        project_root = Path(__file__).resolve().parents[2]
        candidate = project_root / "database" / "schema.sql"
        tried.append(str(candidate))
        if candidate.is_file():
            ddl = candidate.read_text(encoding="utf-8")
            with self._conn:
                self._conn.executescript(ddl)
            logger.info("✅ Loaded schema from %s", candidate)
            return

        # 3) fallback: alongside this module
        fallback = Path(__file__).resolve().with_name("schema.sql")
        tried.append(str(fallback))
        if fallback.is_file():
            ddl = fallback.read_text(encoding="utf-8")
            with self._conn:
                self._conn.executescript(ddl)
            logger.info("✅ Loaded schema from %s", fallback)
            return

        raise FileNotFoundError(f"schema.sql not found. Tried: {tried}")

    def connection(self) -> sqlite3.Connection:
        return self._conn

    def execute(self, fn):
        with self._lock:
            return fn(self._conn)
