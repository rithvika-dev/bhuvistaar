from app.database import engine
from sqlalchemy import text

statements = [
    "ALTER TABLE harmonized_features ADD COLUMN IF NOT EXISTS match_id INTEGER;",
    "ALTER TABLE harmonized_features ADD COLUMN IF NOT EXISTS source_info TEXT;",
]

with engine.begin() as conn:
    for stmt in statements:
        try:
            conn.execute(text(stmt))
            print("OK", stmt)
        except Exception as exc:
            print("ERR", stmt, type(exc).__name__, exc)

print("Schema fix complete.")
