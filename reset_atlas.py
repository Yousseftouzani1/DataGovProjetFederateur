
import os
from pymongo import MongoClient
import certifi

# Hardcoded URI from .env since we are running this as a standalone script
MONGO_URI = "mongodb+srv://projetFD:ensias2025@datagovdb.sjhsdum.mongodb.net/?retryWrites=true&w=majority&appName=DataGovDB"
DB_NAME = "DataGovDB"

def reset_db():
    print(f"🔌 Connecting to remote Atlas DB: {DB_NAME}...")
    try:
        # ca = certifi.where() # sometimes needed for SSL
        client = MongoClient(MONGO_URI, tls=True)
        db = client[DB_NAME]
        
        # Check count before
        count = db.tasks.count_documents({})
        print(f"📊 Current Task Count: {count}")
        
        if count > 0:
            print("🗑️ Dropping 'tasks' collection...")
            db.tasks.drop()
            print("✅ 'tasks' collection dropped successfully.")
        else:
            print("✨ Collection already empty.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_db()
