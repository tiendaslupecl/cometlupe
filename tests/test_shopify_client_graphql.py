import os
import unittest
from unittest.mock import patch

os.environ["SHOP_DOMAIN"] = "example.myshopify.com"
os.environ["ADMIN_API_TOKEN"] = "dummy_token"

import shopify_client


class _Resp:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class GraphqlRetryTests(unittest.TestCase):
    def test_graphql_raises_after_persistent_429(self):
        with patch.object(shopify_client.requests, "post", return_value=_Resp(429)), patch.object(
            shopify_client.time, "sleep"
        ):
            with self.assertRaises(Exception) as ctx:
                shopify_client.graphql("query { shop { name } }", max_retries=2)
        self.assertIn("HTTP 429 persistente", str(ctx.exception))

    def test_graphql_succeeds_after_rate_limit_retry(self):
        responses = [
            _Resp(429),
            _Resp(200, {"data": {"shop": {"name": "Demo"}}}),
        ]
        with patch.object(
            shopify_client.requests, "post", side_effect=responses
        ) as post_mock, patch.object(shopify_client.time, "sleep"):
            data = shopify_client.graphql("query { shop { name } }", max_retries=2)
        self.assertEqual(data["shop"]["name"], "Demo")
        self.assertEqual(post_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
