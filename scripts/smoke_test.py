"""ShopSecure v1 smoke test. Standard library only, so it runs on any Python 3.
Usage (from the project root):  python scripts/smoke_test.py
It checks that the app works, then confirms the deliberately seeded design flaws.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

GATEWAY = "http://localhost:18080/api"
PAYMENTS = "http://localhost:18002"
results = []


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as e:  # connection refused, timeout, ...
        return None, str(e)


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


print("== 1. The app works ==")
s, b = call("GET", f"{GATEWAY}/health")
check("gateway -> orders-api health", s == 200, f"(status {s})")
if s != 200:
    print("\nStack is not reachable. Run 'docker compose ps' and see the runbook troubleshooting section.")
    sys.exit(1)

user = "user_" + uuid.uuid4().hex[:6]
s, b = call("POST", f"{GATEWAY}/register", {"username": user, "password": "Passw0rd!"})
check("register", s == 200, f"(status {s})")
user_id = b.get("id") if isinstance(b, dict) else None
s, b = call("POST", f"{GATEWAY}/login", {"username": user, "password": "Passw0rd!"})
check("login returns a token", s == 200 and "access_token" in (b or {}), f"(status {s})")
s, b = call("GET", f"{GATEWAY}/products?search=lap")
check("product search", s == 200 and len(b) >= 1, f"(found {len(b) if isinstance(b, list) else 0})")
s, b = call("POST", f"{GATEWAY}/orders",
            {"user_id": user_id, "product_id": 1, "quantity": 1, "card_number": "4111111111111111"})
check("create order (calls payments-svc)", s == 200 and b.get("status") == "approved", f"(status {s}, {b})")
order_id = b.get("order_id") if isinstance(b, dict) else 1

print("\n== 2. Seeded design flaws (these SHOULD be confirmed in v1) ==")
s, b = call("GET", f"{PAYMENTS}/health")
check("FLAW 1: payments-svc reachable directly from the host, bypassing the gateway", s == 200, f"(status {s})")

s, b = call("POST", f"{PAYMENTS}/charge", {"order_id": 0, "amount": 1.0, "card_number": "4111111111111111"})
check("FLAW 3: payments-svc accepts calls with no authentication", s == 200 and b.get("status") == "approved",
      f"(status {s})")

payload = urllib.parse.quote("' UNION SELECT id, username || ':' || password_hash, 0 FROM users --")
s, b = call("GET", f"{GATEWAY}/products?search={payload}")
check("CODE FLAW: SQL injection leaks usernames and password hashes",
      s == 200 and isinstance(b, list) and any(user in str(row.get('name')) for row in b))

s, b = call("GET", f"{GATEWAY}/orders/{order_id}")
check("CODE FLAW: anyone can read any order with no login (broken access control)", s == 200, f"(status {s})")

print("\nFlaws 2 (plain HTTP between services) and 4 (admin DB account) are design facts.")
print("Confirm them with the commands in the runbook, section 'Confirm flaws 2 and 4'.")
passed, total = sum(results), len(results)
print(f"\n{passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
