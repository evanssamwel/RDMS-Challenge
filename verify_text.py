
import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost:5000/api"

def request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req.data = json_data
        
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_text():
    print("Testing TEXT Feature...")
    
    table_name = f"test_text_{int(time.time())}"
    create_payload = {
        "name": table_name,
        "columns": [
            {"name": "id", "type": "INT", "pk": True},
            {"name": "content", "type": "TEXT"}
        ]
    }
    
    print(f"Creating table {table_name}...")
    res = request('POST', "/tables/create", create_payload)
    if not res or not res.get('success'):
        print(f"FAILED to create table")
        return False
    print("Table created.")
    
    print("Inserting data...")
    insert_payload = {
        "id": 1,
        "content": "This is a very long text content.\nIt has newlines and 'quotes'." * 5
    }
    
    res = request('POST', f"/table/{table_name}", insert_payload)
    if not res or not res.get('success'):
         print(f"FAILED to insert")
         return False
    print("Row inserted.")
    return True

if __name__ == "__main__":
    if test_text():
        print("\nSUCCESS: TEXT feature verified!")
    else:
        print("\nFAILURE: TEXT verification failed.")
