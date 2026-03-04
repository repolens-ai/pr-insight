import hashlib
import hmac
import pytest
from fastapi import HTTPException

from pr_insight.servers.utils import DefaultDictWithTimeout, RateLimitExceeded, verify_signature


class TestVerifySignature:
    def test_valid_signature(self):
        payload = b'{"test": "data"}'
        secret = "mysecret"
        hash_object = hmac.new(secret.encode('utf-8'), msg=payload, digestmod=hashlib.sha256)
        signature = "sha256=" + hash_object.hexdigest()
        
        result = verify_signature(payload, secret, signature)
        assert result is None

    def test_missing_signature_header(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_signature(b'{"test": "data"}', "secret", None)
        assert exc_info.value.status_code == 403
        assert "missing" in exc_info.value.detail.lower()

    def test_invalid_signature(self):
        payload = b'{"test": "data"}'
        with pytest.raises(HTTPException) as exc_info:
            verify_signature(payload, "secret", "sha256=invalid")
        assert exc_info.value.status_code == 403
        assert "didn't match" in exc_info.value.detail.lower()


class TestDefaultDictWithTimeout:
    def test_basic_get_set(self):
        d = DefaultDictWithTimeout(list, ttl=60)
        d["key"].append("value")
        assert d["key"] == ["value"]

    def test_no_ttl(self):
        d = DefaultDictWithTimeout(list)
        d["key"].append("value")
        assert d["key"] == ["value"]
        d["key"].append("value2")
        assert d["key"] == ["value", "value2"]

    def test_delete_key(self):
        d = DefaultDictWithTimeout(list)
        d["key"].append("value")
        assert "key" in d._DefaultDictWithTimeout__key_times
        del d["key"]
        assert "key" not in d._DefaultDictWithTimeout__key_times
