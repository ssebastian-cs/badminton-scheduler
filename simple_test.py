import urllib.request
import urllib.error
import json

# Test 404 error
try:
    urllib.request.urlopen('http://127.0.0.1:5000/nonexistent')
except urllib.error.HTTPError as e:
    print(f'Got expected 404: {e.code}')

# Check health after error
response = urllib.request.urlopen('http://127.0.0.1:5000/health')
data = json.loads(response.read().decode())
print(f'Health Status: {data.get("status")}')
print(f'Error Count: {data.get("errors", {}).get("last_hour_count", 0)}')