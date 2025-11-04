-- Enable basics
PRAGMA foreign_keys = ON;

-- Base lookup for multi-chat/platform support
CREATE TABLE IF NOT EXISTS chats (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE          -- e.g., 'discord', 'slack'
);

-- Default chat: Discord = 1
INSERT OR IGNORE INTO chats (id, name) VALUES (1, 'discord');

-- Users keyed by platform user id (Discord user id as text)
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY
);

-- Reminders with FK to users and chat
CREATE TABLE IF NOT EXISTS reminders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT    NOT NULL,
    chat_id    INTEGER NOT NULL DEFAULT 1,
    label      TEXT    NOT NULL,
    persona    TEXT    NOT NULL,
    time_hhmm  TEXT    NOT NULL,      -- 'HH:MM' 24h
    active     INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

CREATE INDEX IF NOT EXISTS ix_reminders_user_time
ON reminders(user_id, time_hhmm);
