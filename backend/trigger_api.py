
import requests
import json
import time

def trigger_schedule():
    rota_id = "22222222-2222-2222-2222-222222222222"
    url = f"http://localhost:5000/api/schedule/{rota_id}"
    
    print(f"🚀 Triggering schedule generation for {rota_id} via API...")
    try:
        # Increase timeout because generation takes time
        response = requests.post(url, timeout=300)
        
        if response.status_code == 200:
            print("✅ Success!")
            data = response.json()
            # Check summary for hours
            if "summary" in data:
                print("Summary:", json.dumps(data["summary"], indent=2))
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    trigger_schedule()
