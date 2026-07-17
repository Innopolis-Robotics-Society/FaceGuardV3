import os

# A deterministic, non-production secret makes security imports explicit in tests.
os.environ["JWT_SECRET"] = "faceguard-test-signing-secret-not-for-production-2026"
