import time
import statistics
import requests

BASE = "http://localhost:8000"


def get_token(email: str, password: str) -> str:
    r = requests.post(f"{BASE}/auth/token", data={"username": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def run_query(token: str, q: str) -> float:
    t0 = time.time()
    r = requests.post(
        f"{BASE}/query",
        json={"query": q},
        headers={"Authorization": f"Bearer {token}"},
        timeout=600,
    )
    r.raise_for_status()
    return time.time() - t0


if __name__ == "__main__":
    token = get_token("user1@example.com", "pass1")

    queries = [
        "What did Sarah say about the Q4 budget?",
        "Show me emails discussing the API integration project",
        "When did I last hear from the marketing team?",
        "Summarize all conversations about the product launch",
    ]

    times = [run_query(token, q) for q in queries]
    times_sorted = sorted(times)

    print("n =", len(times))
    print("p50 =", statistics.median(times))
    print("p95 ~= ", times_sorted[max(0, int(0.95 * len(times)) - 1)])
    print("avg =", sum(times) / len(times))

