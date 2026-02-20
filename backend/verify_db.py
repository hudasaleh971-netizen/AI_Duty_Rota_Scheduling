
from src.tools.supabase_tool import get_client
import json

def verify_db():
    try:
        client = get_client()
        response = client.table("schedule_assignments").select("*").execute()
        
        # Check if table exists (implicit by success) and count rows
        data = response.data
        count = len(data)
        
        print(f"✅ DB Connection Successful")
        print(f"📊 Table 'schedule_assignments' has {count} rows.")
        
        if count > 0:
            print("📝 Sample Data:")
            print(json.dumps(data[0], indent=2))
        else:
            print("⚠️ Table is empty (Persistence might not have finished yet).")
            
    except Exception as e:
        print(f"❌ Error querying DB: {e}")

if __name__ == "__main__":
    verify_db()
