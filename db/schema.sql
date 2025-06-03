-- Table: Funders
CREATE TABLE IF NOT EXISTS funders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,             
    name TEXT NOT NULL,               -- e.g., "W.K. Kellogg Foundation"
    type TEXT,                        -- e.g., "private", "federal", "state"
    contact_email TEXT,
    notes TEXT
);



-- Table: Grants
CREATE TABLE IF NOT EXISTS grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- e.g., 1
    name TEXT NOT NULL UNIQUE,               -- e.g., "Baker 2024"
    funder_id INTEGER,                   -- FK to funders(id)
    start_date DATE,
    end_date DATE,
    status TEXT,                      -- e.g., "active", "closed"
    notes TEXT,
    FOREIGN KEY (funder_id) REFERENCES funders(id)
);

-- Table: Grant Line Items
CREATE TABLE IF NOT EXISTS grant_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- e.g., LI001
    grant_id TEXT,
    name TEXT NOT NULL,               -- e.g., "Salaries & Fringe"
    description TEXT,
    FOREIGN KEY (grant_id) REFERENCES grants(id)
);


-- Table: Mapping QB codes to Grant-specific Line Items
CREATE TABLE IF NOT EXISTS qb_to_grant_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grant_id TEXT,
    qb_code TEXT,
    grant_line_item_id INTEGER,
    FOREIGN KEY (grant_id) REFERENCES grants(id),
    FOREIGN KEY (qb_code) REFERENCES qb_accounts(code),
    FOREIGN KEY (grant_line_item_id) REFERENCES grant_line_items(id)
);




-- Table: Parent Categories e.g., 'Expenses', 'Income
CREATE TABLE IF NOT EXISTS qb_parent_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- e.g., 1
    name TEXT NOT NULL UNIQUE,               -- e.g., "Personnel"
    description TEXT
);

-- Table: Mid-Level Categories e.g., 'General Expenses', 'Personnel Costs', 'Expenses'
CREATE TABLE IF NOT EXISTS qb_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- e.g., 1
    name TEXT NOT NULL,               -- e.g., "Salaries & Fringe"
    parent_id INTEGER,              -- FK to qb_parent_categories(id)
    FOREIGN KEY (parent_id) REFERENCES qb_parent_categories(id)
);

-- Table: Leaf Level QB Accounts e.g. 8707 Professional Development
-- This table holds the actual QuickBooks account codes and names.
CREATE TABLE IF NOT EXISTS qb_accounts (
    code TEXT PRIMARY KEY,            -- e.g., "8705"
    name TEXT NOT NULL,                        -- e.g., "Workshops"
    category_id INTEGER NOT NULL,              -- e.g., "Conferences and Meetings"
    FOREIGN KEY (category_id) REFERENCES qb_categories(id)
);


-- Table: Monthly Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grant_id TEXT,
    month TEXT,                       -- e.g., "2025-06"
    qb_code TEXT,
    amount REAL,
    notes TEXT,
    line_item_id INTEGER, -- FK to grant_line_items(id)
    date_submitted DATE, -- Date when the expense was submitted
    FOREIGN KEY (grant_id) REFERENCES grants(id),
    FOREIGN KEY (qb_code) REFERENCES qb_accounts(code),
    FOREIGN KEY (line_item_id) REFERENCES grant_line_items(id)

);


-- Future: Add tables for GrantYears, FTE allocations, and Team Buckets for reporting.
-- Future: Metrics per Grant and Outcomes/Goals
