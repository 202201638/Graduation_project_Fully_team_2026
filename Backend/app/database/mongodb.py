from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/medical_system")
# Extract database name from URL or use default
if "/" in MONGODB_URL.split("//")[-1]:
    # Database name is included in URL
    DATABASE_NAME = MONGODB_URL.split("/")[-1]
else:
    # Use separate database name
    DATABASE_NAME = os.getenv("DATABASE_NAME", "medical_system")

client = None
database = None

async def connect_to_mongodb():
    """Connect to MongoDB"""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        # Test the connection
        await client.admin.command('ping')
        database = client[DATABASE_NAME]
        print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")

async def create_indexes():
    """Create database indexes"""
    try:
        # Users collection indexes
        await database.users.create_index("email", unique=True)
        await database.users.create_index("user_id")
        
        # Patients collection indexes
        await database.patients.create_index("patient_id", unique=True)
        await database.patients.create_index("user_id")
        
        # X-ray analysis collection indexes
        await database.xray_analyses.create_index("analysis_id", unique=True)
        await database.xray_analyses.create_index("patient_id")
        await database.xray_analyses.create_index("created_at")
        
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not create indexes: {e}")

def get_database():
    """Get database instance"""
    return database
