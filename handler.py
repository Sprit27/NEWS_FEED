from UpdatN import NewsExtractor
from pymongo import MongoClient
import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

#------------------------------------------------------------------------------------------------------------------------

try:
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["news_db"]
    collection = db["daily_news"]
    
    # Test connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas")
    
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    exit(1)

#--------------------------------------------------------------------------------------------------------------------------------

feed = NewsExtractor()
result = feed.feed("https://timesofindia.indiatimes.com","https://sputniknews.in","https://www.euronews.com/")

#-------------------------------------------------------------------------------------------------------------------------------------

if result and len(result) == 2:
    state, nc = result
    
    if state == "\n--- SUCCESSFULLY EXTRACTED NEWS (JSON) ---":
        try:
            collection.delete_many({})  # Clear old news
            collection.insert_one({"date": datetime.datetime.now(), "news": nc})
            print("✅ News updated in MongoDB Atlas")
        except Exception as e:
            print(f"❌ Failed to insert into MongoDB: {e}")
    else:
        print("❌ Failed to extract news - no data to upload to MongoDB")
        print(f"State: {state}")
        if len(result) == 2:
            print(f"Error details: {nc}")
else:
    print("❌ Feed method didn't return expected data format")


