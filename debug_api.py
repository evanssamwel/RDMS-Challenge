
import urllib.request
import json

try:
    with urllib.request.urlopen("http://localhost:5000/api/tables") as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Status: {response.getcode()}")
        print(f"Data: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
