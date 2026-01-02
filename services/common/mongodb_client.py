"""
MongoDB Client for DataGov Services
Provides connection to MongoDB Atlas database
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DATABASE_NAME", "DataGovDB")

class MongoDBClient:
    """Singleton MongoDB client for all services"""
    
    _client = None
    _db = None
    
    @classmethod
    def get_connection(cls):
        """Get MongoDB client connection"""
        if cls._client is None:
            if not MONGO_URI:
                raise ValueError("MONGODB_URI not found in environment variables")
            cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            cls._db = cls._client[DB_NAME]
        return cls._client
    
    @classmethod
    def get_database(cls):
        """Get DataGovDB database"""
        if cls._db is None:
            cls.get_connection()
        return cls._db
    
    @classmethod
    def get_collection(cls, collection_name):
        """Get specific collection"""
        return cls.get_database()[collection_name]
    
    @classmethod
    def test_connection(cls):
        """Test MongoDB connection"""
        try:
            cls.get_connection().admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            return False
    
    @classmethod
    def close_connection(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

# Quick access functions
def get_db():
    """Get database instance"""
    return MongoDBClient.get_database()

def get_collection(name):
    """Get collection instance"""
    return MongoDBClient.get_collection(name)

def test_connection():
    """Test connection"""
    return MongoDBClient.test_connection()
