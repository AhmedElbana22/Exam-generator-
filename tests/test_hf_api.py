"""
Test HuggingFace API connection.
Run: python tests/test_hf_api.py
"""

from services.hf_api_service import HFApiService


def test_basic_generation():
    print("\n🔌 Testing HuggingFace API connection...")
    api = HFApiService()

    response = api.generate(
        prompt="Say hello in one sentence.",
        system_prompt="You are a friendly assistant.",
        max_tokens=50,
    )

    print(f"✅ Response: {response}")
    assert len(response) > 0


def test_structured_generation():
    print("\n📦 Testing structured JSON output...")
    api = HFApiService()

    response = api.generate_structured(
        prompt='Return a JSON object with keys "name" and "topic". Name is "ImtiQan", topic is "NLP".',
        max_tokens=100,
    )

    print(f"✅ Structured response: {response}")
    assert "{" in response


if __name__ == "__main__":
    test_basic_generation()
    test_structured_generation()
    print("\n🎉 All API tests passed!")