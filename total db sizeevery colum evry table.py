from app import app
from extensions import db
from sqlalchemy import inspect, text
import os

with app.app_context():
    inspector = inspect(db.engine)

    tables = inspector.get_table_names()
    
    for table_name in tables:
        print(f"\nTable: {table_name}")
        print("-" * (len(table_name) + 7))
        
        columns = inspector.get_columns(table_name)
        
        for col in columns:
            name = col['name']
            col_type = str(col['type'])
            nullable = col['nullable']
            
            # Try to get max length for strings
            size = getattr(col['type'], 'length', None)
            
            # Calculate approximate storage size in DB
            try:
                if "CHAR" in col_type.upper() or "TEXT" in col_type.upper():
                    # For strings, sum the length of stored values
                    query = text(f"SELECT SUM(LENGTH({name})) FROM {table_name}")
                    result = db.session.execute(query).scalar()
                elif "BLOB" in col_type.upper() or "BYTEA" in col_type.upper() or "LARGE" in col_type.upper():
                    # For binary, sum the length in bytes
                    query = text(f"SELECT SUM(LENGTH({name})) FROM {table_name}")
                    result = db.session.execute(query).scalar()
                else:
                    result = None
            except Exception as e:
                result = None

            print(f"Column: {name}")
            print(f"  Type: {col_type}")
            if size:
                print(f"  Declared Max Length: {size}")
            if result is not None:
                print(f"  Current Storage Size: {result} bytes")
            print(f"  Nullable: {nullable}\n")
    
    # ---------------------------
    # Total SQLite DB File Size
    # ---------------------------
    try:
        db_file = db.engine.url.database  # path to your .db file
        if os.path.exists(db_file):
            total_bytes = os.path.getsize(db_file)
            total_mb = total_bytes / (1024 * 1024)
            total_gb = total_bytes / (1024 * 1024 * 1024)
            print("\n" + "="*40)
            print(f"Total Database File Size: {total_bytes} bytes")
            print(f"Total Database File Size: {total_mb:.2f} MB")
            print(f"Total Database File Size: {total_gb:.4f} GB")
            print("="*40)
        else:
            print("Database file not found.")
    except Exception as e:
        print(f"Could not fetch total database size: {e}")
