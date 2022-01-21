CREATE TABLE users (
  id INTEGER,
  name TEXT NOT NULL,
  token TEXT NOT NULL,
  webhook_url TEXT,
  UNIQUE(name),
  UNIQUE(token),
  PRIMARY KEY (id)
);
