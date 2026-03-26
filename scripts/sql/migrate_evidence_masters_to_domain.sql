-- Evidence masters: domain scope (run after backing up the DB).
-- Applies when evidence_masters still has a legacy tool_id column from older app versions.

-- 1) Backfill domain from tools
UPDATE evidence_masters em
SET domain_id = t.domain_id
FROM tools t
WHERE em.tool_id IS NOT NULL
  AND em.tool_id = t.id
  AND t.domain_id IS NOT NULL
  AND (em.domain_id IS NULL OR em.domain_id IS DISTINCT FROM t.domain_id);

-- 2) Optional: drop legacy column (uncomment when ORM and app no longer reference tool_id)
-- ALTER TABLE evidence_masters DROP CONSTRAINT IF EXISTS evidence_masters_tool_id_foreign;
-- ALTER TABLE evidence_masters DROP COLUMN IF EXISTS tool_id;
