PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects(
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    room                    TEXT NOT NULL,
    budget                  INTEGER NOT NULL CHECK (budget >= 0),
    start_date              TEXT NOT NULL,
    target_completion_date  TEXT NOT NULL,
    project_status          TEXT NOT NULL DEFAULT 'planning' 
                            CHECK (project_status IN ('planning', 'in_progress', 'on_hold', 'completed', 'cancelled'))  
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks(
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    description             TEXT NOT NULL,
    est_cost                INTEGER NOT NULL CHECK (est_cost >= 0),
    actual_cost             INTEGER CHECK (actual_cost IS NULL OR actual_cost >=0),
    trade_category          TEXT NOT NULL 
                            CHECK (trade_category IN ('plumbing', 'electrical', 'carpentry', 'hvac', 'demolition', 'painting', 'flooring', 'general')),
    task_status             TEXT NOT NULL DEFAULT 'todo'
                            CHECK (task_status IN ('todo', 'in_progress', 'blocked', 'done')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT                        
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(task_status);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(project_status);