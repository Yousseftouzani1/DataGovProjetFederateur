import json
from pymongo import MongoClient

# --------------------------------
# CONFIGURATION
# --------------------------------
MONGO_URI = "mongodb://localhost:27017"  # or Atlas URI
DB_NAME = "taxonomy_db"
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
