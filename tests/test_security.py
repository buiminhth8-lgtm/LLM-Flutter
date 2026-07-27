from llm_studio.security import hash_api_key, redact_secret


def test_api_key_hash_is_not_plaintext():
    key = "sk-llmstudio-secret"
    assert hash_api_key(key) != key


def test_redact_secret_masks_middle():
    assert redact_secret("abcdefghijkl") == "abcd...ijkl"
