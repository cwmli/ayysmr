/*
 * Clear all table data
 */
DELETE FROM "Users";
DELETE FROM "Tracks";
/* 
 * Users table test data
 */
INSERT INTO "Users" VALUES ('existingid', 'oldtoken', 'oldtoken', 0, CURRENT_TIMESTAMP);