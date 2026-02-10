import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# --------------------------------
# CONFIGURATION
# --------------------------------
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise RuntimeError("MONGODB_URI environment variable is required. Set it in .env file.")
DB_NAME = os.getenv("DATABASE_NAME", "DataGovDB")
COLLECTION_NAME = "banking_taxonomy"
JSON_FILE_PATH = "taxonomie.json"   # your file name

# --------------------------------
# CONNECT TO MONGODB
# --------------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --------------------------------
# LOAD JSON FILE
# --------------------------------
with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
    document = json.load(file)

# --------------------------------
# INSERT INTO MONGODB
# --------------------------------
result = collection.insert_one(document)

print(f"Inserted document with ID: {result.inserted_id}")
