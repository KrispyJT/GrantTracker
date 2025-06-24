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
    total_award REAL,
    status TEXT,                      -- e.g., "active", "closed", "Pending"
    notes TEXT,
    FOREIGN KEY (funder_id) REFERENCES funders(id)
);

-- -- Table: Grant Line Items
-- CREATE TABLE IF NOT EXISTS grant_line_items (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,              
--     grant_id INTEGER,
--     name TEXT NOT NULL,               -- e.g., "Salaries & Fringe"
--     description TEXT,
--     allocated_amount, REAL DEFAULT 0.0,
--     FOREIGN KEY (grant_id) REFERENCES grants(id) ON DELETE CASCADE
-- );

-- Table: Grant Line Items
CREATE TABLE IF NOT EXISTS grant_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              
    grant_id INTEGER,
    name TEXT NOT NULL,               -- e.g., "Salaries & Fringe"
    description TEXT,
    allocated_amount REAL DEFAULT 0.0,
    FOREIGN KEY (grant_id) REFERENCES grants(id) ON DELETE CASCADE,
    UNIQUE(grant_id, name)  -- Ensure each grant has unique line item names
);


-- -- Table: Mapping QB codes to Grant-specific Line Items
-- CREATE TABLE IF NOT EXISTS qb_to_grant_mapping (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     grant_id INTEGER,
--     qb_code TEXT,
--     grant_line_item_id INTEGER,
--     FOREIGN KEY (grant_id) REFERENCES grants(id) ON DELETE CASCADE,
--     FOREIGN KEY (qb_code) REFERENCES qb_accounts(code),
--     FOREIGN KEY (grant_line_item_id) REFERENCES grant_line_items(id) ON DELETE CASCADE
-- );

-- Table: Mapping QB codes to Grant-specific Line Items
CREATE TABLE IF NOT EXISTS qb_to_grant_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grant_id INTEGER,
    qb_code TEXT,
    grant_line_item_id INTEGER,
    FOREIGN KEY (grant_id) REFERENCES grants(id) ON DELETE CASCADE,
    FOREIGN KEY (qb_code) REFERENCES qb_accounts(code),
    FOREIGN KEY (grant_line_item_id) REFERENCES grant_line_items(id) ON DELETE CASCADE,
    UNIQUE(grant_id, qb_code, grant_line_item_id)  -- Prevent duplicate mappings
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
    FOREIGN KEY (parent_id) REFERENCES qb_parent_categories(id) ON DELETE CASCADE
);

-- Table: Leaf Level QB Accounts e.g. 8707 Professional Development
-- This table holds the actual QuickBooks account codes and names.
CREATE TABLE IF NOT EXISTS qb_accounts (
    code TEXT PRIMARY KEY,            -- e.g., "8705"
    name TEXT NOT NULL,                        -- e.g., "Workshops"
    category_id INTEGER NOT NULL,              -- e.g., "Conferences and Meetings"
    FOREIGN KEY (category_id) REFERENCES qb_categories(id) ON DELETE CASCADE
);


-- Table: Monthly Actual Expenses
CREATE TABLE IF NOT EXISTS actual_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grant_id INTEGER NOT NULL,
    month TEXT,                       -- e.g., "2025-06"
    qb_code TEXT,
    amount REAL,
    notes TEXT,
    line_item_id INTEGER, -- FK to grant_line_items(id)
    date_submitted DATE, -- Date when the expense was submitted
    FOREIGN KEY (grant_id) REFERENCES grants(id) ON DELETE CASCADE,
    FOREIGN KEY (qb_code) REFERENCES qb_accounts(code),
    FOREIGN KEY (line_item_id) REFERENCES grant_line_items(id) ON DELETE CASCADE

);


-- Table: Monthly Anticipated Expenses
CREATE TABLE IF NOT EXISTS anticipated_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grant_id INTEGER,
    line_item_id INTEGER,
    month TEXT,
    expected_amount REAL,
    FOREIGN KEY (grant_id) REFERENCES grants(id) ON DELETE CASCADE,
    FOREIGN KEY (line_item_id) REFERENCES grant_line_items(id) ON DELETE CASCADE
); 



-- Future: Add tables for GrantYears, FTE allocations, and Team Buckets for reporting.
-- Future: Metrics per Grant and Outcomes/Goals


-- When joining grants to funders, line items, or filtering by grant
-- CREATE INDEX idx_grants_funder_id ON grants(funder_id);

-- -- When looking up line items by grant
-- CREATE INDEX idx_lineitems_grant_id ON grant_line_items(grant_id);

-- -- When mapping codes to grant items
-- CREATE INDEX idx_mapping_grant ON qb_to_grant_mapping(grant_id);
-- CREATE INDEX idx_mapping_line_item ON qb_to_grant_mapping(grant_line_item_id);

-- -- When filtering expenses by grant or month
-- CREATE INDEX IF NOT EXISTS idx_expenses_grant_month ON actual_expenses(grant_id, month);


-- -- CREATE INDEX idx_expenses_grant_month ON anticipated_expenses(grant_id, month);

-- -- When looking up QB codes quickly
-- CREATE INDEX idx_qb_accounts_code ON qb_accounts(code);

-- CREATE INDEX idx_expenses_line_item ON actual_expenses(line_item_id);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_grants_funder_id ON grants(funder_id);
CREATE INDEX IF NOT EXISTS idx_lineitems_grant_id ON grant_line_items(grant_id);
CREATE INDEX IF NOT EXISTS idx_mapping_grant ON qb_to_grant_mapping(grant_id);
CREATE INDEX IF NOT EXISTS idx_mapping_line_item ON qb_to_grant_mapping(grant_line_item_id);
CREATE INDEX IF NOT EXISTS idx_expenses_grant_month ON actual_expenses(grant_id, month);
CREATE INDEX IF NOT EXISTS idx_qb_accounts_code ON qb_accounts(code);
CREATE INDEX IF NOT EXISTS idx_expenses_line_item ON actual_expenses(line_item_id);
CREATE INDEX IF NOT EXISTS idx_anticipated_lookup ON anticipated_expenses(grant_id, line_item_id, month);