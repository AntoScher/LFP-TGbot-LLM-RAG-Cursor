from flask_app import create_app, db
from flask_app.models import SessionLog

def update_database():
    print("Updating database schema...")
    app = create_app()
    
    with app.app_context():
        # This will add the new username column if it doesn't exist
        try:
            # For SQLite, we need to use ALTER TABLE
            with db.engine.connect() as conn:
                # Check if the column already exists
                result = conn.execute(
                    "PRAGMA table_info(sessions);"
                ).fetchall()
                
                # Check if 'username' column exists
                columns = [row[1] for row in result]
                if 'username' not in columns:
                    print("Adding 'username' column to 'sessions' table...")
                    conn.execute("ALTER TABLE sessions ADD COLUMN username VARCHAR(100);")
                    print("Successfully updated database schema!")
                else:
                    print("The 'username' column already exists in the 'sessions' table.")
                    
        except Exception as e:
            print(f"Error updating database schema: {e}")
            print("Falling back to recreating the database...")
            
            # If ALTER TABLE fails, recreate the tables
            db.drop_all()
            db.create_all()
            print("Database recreated with the new schema.")

if __name__ == "__main__":
    update_database()
