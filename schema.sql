CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        shortcode TEXT,
        author TEXT,
        caption TEXT,
        image BLOB,
        video BLOB,
        posted_at TEXT,
        likes INTEGER,
        title TEXT,
        folder TEXT
);

CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
);
