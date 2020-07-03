ALTER TABLE bakchods
	RENAME COLUMN censored TO modifiers;

UPDATE bakchods
SET modifiers = "{}";