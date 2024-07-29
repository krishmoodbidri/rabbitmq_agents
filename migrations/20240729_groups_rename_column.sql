BEGIN TRANSACTION;

-- Create new table with updated_by column
CREATE TABLE groups_temp (
        id INTEGER PRIMARY KEY,
        user TEXT,
        "group" TEXT,
        operation INTEGER,
        date DATETIME,
        host TEXT,
        updated_by TEXT,
        interface TEXT
);

-- Copy all entries from old table
INSERT INTO groups_temp(user,"group",operation,date,host,updated_by,interface)
SELECT user,"group",operation,date,host,executed_by,interface
FROM groups;

-- Drop old table
DROP TABLE groups;

-- Rename new table
ALTER TABLE groups_temp
RENAME TO groups;

COMMIT;
