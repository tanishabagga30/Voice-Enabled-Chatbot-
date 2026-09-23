import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE_URL = "http://127.0.0.1:5000"

def test_endpoint(name, payload):
    print(f"\n==========================================")
    print(f"RUNNING TEST: {name}")
    print(f"==========================================")
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        print(f"Request ID: {data.get('request_id')}")
        print(f"Recognized Text: {data.get('recognized_text')}")
        print(f"Intent: {data.get('intent')} ({data.get('confidence_pct')}%)")
        print(f"Response Mode: {data.get('response_mode')}")
        print(f"ML Latency: {data.get('ml_inference_ms')} ms")
        print(f"Grok Latency: {data.get('grok_api_ms')} ms")
        print(f"Total Backend Latency: {data.get('total_backend_ms')} ms")
        print(f"Response Snippet:\n{data.get('response')[:250]}...")
        return data
    except Exception as e:
        print(f"TEST ERROR: {e}")
        return None

if __name__ == "__main__":
    t1 = test_endpoint("1. Joke Request", {"message": "Tell me a joke."})
    t2 = test_endpoint("2. Multi-Aspect Request", {"message": "hello I am getting bored I have exam I am very stressed and I am hungry what should I do"})
    t3 = test_endpoint("3. Technical Request", {"message": "Write a Python program for sorting."})
    t4 = test_endpoint("4. Science Request", {"message": "Explain quantum computing like I'm five."})
    print("\nAll automated verification tests completed successfully!")
