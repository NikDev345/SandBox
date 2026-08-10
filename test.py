import asyncio
import time

from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest

# -----------------------------
# TEST 1: Basic request
# -----------------------------
async def test_basic():
    print("\n--- TEST 1: BASIC ---")
    req = LLMRequest(prompt="Say hello in one sentence")
    res = await gateway.generate(req)
    print("Response:", res.text)
    print("Provider:", res.provider)


# -----------------------------
# TEST 2: Cache test
# -----------------------------
async def test_cache():
    print("\n--- TEST 2: CACHE ---")

    req = LLMRequest(prompt="What is AI?")
    res1 = await gateway.generate(req)
    print("First call cached?", res1.cached)

    res2 = await gateway.generate(req)
    print("Second call cached?", res2.cached)


# -----------------------------
# TEST 3: Key rotation
# -----------------------------
async def test_key_rotation():
    print("\n--- TEST 3: KEY ROTATION ---")

    for i in range(5):
        req = LLMRequest(prompt=f"Test rotation {i}")
        res = await gateway.generate(req)
        print(f"Call {i} → Provider:", res.provider)


# -----------------------------
# TEST 4: Retry mechanism
# -----------------------------
async def test_retry():
    print("\n--- TEST 4: RETRY ---")

    # Use a bad model to force retry
    req = LLMRequest(prompt="Hello")
    req.model = "invalid-model"

    try:
        await gateway.generate(req)
    except Exception as e:
        print("Retry triggered. Final error:", str(e))


# -----------------------------
# TEST 5: Provider fallback
# -----------------------------
async def test_fallback():
    print("\n--- TEST 5: FALLBACK ---")

    # Force Gemini failure
    req = LLMRequest(prompt="Hello fallback test")
    req.provider = None  # allow fallback

    # Temporarily break Gemini keys
    for state in gateway.key_states["gemini"]:
        state.healthy = False

    res = await gateway.generate(req)

    print("Response:", res.text)
    print("Provider used:", res.provider)  # should be openai


# -----------------------------
# TEST 6: Unhealthy recovery
# -----------------------------
async def test_recovery():
    print("\n--- TEST 6: RECOVERY ---")

    # Mark Gemini unhealthy
    for state in gateway.key_states["gemini"]:
        state.healthy = False

    # After cooldown simulate recovery
    for state in gateway.key_states["gemini"]:
        state.disabled_until = None
        state.healthy = True

    req = LLMRequest(prompt="Recovery test")
    res = await gateway.generate(req)

    print("Provider:", res.provider)


# -----------------------------
# TEST 7: Load test (parallel)
# -----------------------------
async def test_load():
    print("\n--- TEST 7: LOAD TEST ---")

    async def call(i):
        req = LLMRequest(prompt=f"Load test {i}")
        res = await gateway.generate(req)
        return res.provider

    results = await asyncio.gather(*[call(i) for i in range(10)])
    print("Providers used:", results)


# -----------------------------
# TEST 8: Metrics
# -----------------------------
def test_metrics():
    print("\n--- TEST 8: METRICS ---")
    metrics = gateway.get_metrics()
    for k, v in metrics.items():
        print(k, ":", v)


# -----------------------------
# RUN ALL TESTS
# -----------------------------
async def main():
    await test_basic()
    await test_cache()
    await test_key_rotation()
    await test_retry()
    await test_fallback()
    await test_recovery()
    await test_load()
    test_metrics()


if __name__ == "__main__":
    asyncio.run(main())