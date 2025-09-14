from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(
    MONGO_URI,
    tls=True,  # enable SSL/TLS
    tlsAllowInvalidCertificates=True  # only for local dev/testing, remove in production
)
db = client[DB_NAME]
users_collection = db["users"]
