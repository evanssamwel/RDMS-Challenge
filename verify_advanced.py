
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

def test_workflow():
    print("Testing Advanced Features...")
    
    # 1. Create Table with JSON/TEXT
    table_name = f"test_adv_{int(time.time())}"
    create_payload = {
        "name": table_name,
        "columns": [
            {"name": "id", "type": "INT", "pk": True},
            {"name": "metadata", "type": "JSON"},
            {"name": "content", "type": "TEXT"}
        ]
    }
    
    print(f"Creating table {table_name}...")
    res = request('POST', "/tables/create", create_payload)
    if not res or not res.get('success'):
        print(f"FAILED to create table")
        return False
    print("Table created.")
    
    # 2. Insert Data
    print("Inserting data...")
    # JSON as string
    insert_payload_str = {
        "id": 1,
        "metadata": json.dumps({"active": True}),
        "content": "This is a very long text content." * 5
    }
    
    res = request('POST', f"/table/{table_name}", insert_payload_str)
    if not res or not res.get('success'):
         print(f"FAILED to insert")
         return False
    print("Row inserted.")
    
    # 3. Export CSV
    print("Exporting CSV...")
    res = request('GET', f"/table/{table_name}/export")
    if not res or not res.get('success'):
        print(f"FAILED to export")
        return False
        
    csv_content = res.get('csv')
    print(f"CSV Content Length: {len(csv_content)}")
    print(f"CSV Snippet: {csv_content[:100]}...")
    
    # 4. Import CSV
    print("Importing CSV into new table...")
    target_table = f"{table_name}_import"
    create_payload['name'] = target_table
    request('POST', "/tables/create", create_payload)
    
    import_payload = {"csv": csv_content}
    res = request('POST', f"/table/{target_table}/import", import_payload)
    if not res or not res.get('success'):
        print(f"FAILED to import")
        return False
        
    print(f"Import result: {res.get('message')}")
    
    # Verify import count
    res = request('GET', f"/table/{target_table}")
    if res and res.get('count') == 1:
        print("Verification Successful: 1 row found in imported table.")
        return True
    else:
        print(f"Verification Failed: Expected 1 row, found {res.get('count') if res else 'None'}")
        return False

if __name__ == "__main__":
    if test_workflow():
        print("\nSUCCESS: All advanced features verified!")
    else:
        print("\nFAILURE: Verification failed.")
