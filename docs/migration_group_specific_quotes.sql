ALTER TABLE quotes
ADD COLUMN group_id;

UPDATE quotes
SET group_id = "-1001485566688";