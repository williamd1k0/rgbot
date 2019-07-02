from migrations import migrate

migrate("""
ALTER TABLE season ADD COLUMN done bool;
ALTER TABLE season ALTER COLUMN done set DEFAULT false;
UPDATE season set done = false;
""")
