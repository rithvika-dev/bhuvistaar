from sqlalchemy import text
from app.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))

        print("\nDATABASE CONNECTED!")
        print(result.fetchone())

except Exception as e:
    print("\nDATABASE CONNECTION FAILED!")
    print(e)