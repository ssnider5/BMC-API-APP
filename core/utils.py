# core/utils.py
def printResponseError(response):
    """Debug helper to print full response details."""
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.content}")
    print(f"Text: {response.text}")
    print(f"JSON: {response.json() if response.headers.get('Content-Type') == 'application/json' else 'Not a JSON response'}")
    print(f"URL: {response.url}")
    print(f"Elapsed Time: {response.elapsed}")
    print(f"Request Headers: {response.request.headers}")
    print(f"Request Method: {response.request.method}")
    print(f"Request URL: {response.request.url}")

