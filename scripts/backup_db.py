import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def backup_db():
    """
    Performs a local pg_dump of the operational database.
    """
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5434")
    db_name = os.getenv("DB_NAME", "almox_db")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/backup_{db_name}_{timestamp}.sql"
    
    # Ensure backups directory exists
    os.makedirs("backups", exist_ok=True)
    
    print(f"Starting backup for {db_name}...")
    
    # Set PGPASSWORD environment variable for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    
    try:
        # Note: pg_dump must be in the PATH
        subprocess.run([
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", user,
            "-f", backup_file,
            db_name
        ], check=True, env=env)
        print(f"Backup successful: {backup_file}")
    except Exception as e:
        print(f"Backup failed: {e}")

if __name__ == "__main__":
    backup_db()
