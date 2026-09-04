import http.client
import json
import threading
import unittest

from operator_app import (
    LocalOnlyThreadingHTTPServer,
    OperatorHandler,
    REQUEST_TIMEOUT_SECONDS,
    _client_is_loopback,
    _host_header_is_loopback,
    _is_loopback_host,
    _origin_matches_host,
    run,
)


class OperatorLocalSecurityTests(unittest.TestCase):
    def test_loopback_host_classifier_rejects_network_and_dns_names(self):
        for value in ("127.0.0.1", "127.1.2.3", "localhost", "::1", "[::1]"):
            with self.subTest(value=value):
                self.assertTrue(_is_loopback_host(value))
        for value in ("0.0.0.0", "192.168.1.10", "10.0.0.1", "example.com", "localhost.example"):
            with self.subTest(value=value):
                self.assertFalse(_is_loopback_host(value))

    def test_host_header_classifier_blocks_dns_rebinding_authority(self):
        self.assertTrue(_host_header_is_loopback("127.0.0.1:8080"))
        self.assertTrue(_host_header_is_loopback("localhost:8080"))
        self.assertTrue(_host_header_is_loopback("[::1]:8080"))
        self.assertFalse(_host_header_is_loopback("attacker.example:8080"))
        self.assertFalse(_host_header_is_loopback("127.0.0.1@attacker.example"))
        self.assertFalse(_host_header_is_loopback("localhost.example"))
        self.assertFalse(_host_header_is_loopback("127.0.0.1:notaport"))

    def test_state_changing_origin_must_match_exact_local_authority(self):
        host = "127.0.0.1:8080"
        self.assertTrue(_origin_matches_host(None, host))
        self.assertTrue(_origin_matches_host("http://127.0.0.1:8080", host))
        self.assertFalse(_origin_matches_host("http://127.0.0.1:9999", host))
        self.assertFalse(_origin_matches_host("https://evil.example", host))
        self.assertFalse(_origin_matches_host("null", host))

    def test_client_classifier_requires_loopback(self):
        self.assertTrue(_client_is_loopback(("127.0.0.1", 12345)))
        self.assertTrue(_client_is_loopback(("::1", 12345, 0, 0)))
        self.assertFalse(_client_is_loopback(("192.168.1.20", 12345)))

    def test_run_refuses_non_loopback_bind_before_opening_socket(self):
        with self.assertRaisesRegex(ValueError, "loopback-only"):
            run(host="0.0.0.0", port=8080)
        with self.assertRaisesRegex(ValueError, "loopback-only"):
            run(host="192.168.1.20", port=8080)

    def test_request_timeout_is_bounded(self):
        self.assertGreater(REQUEST_TIMEOUT_SECONDS, 0)
        self.assertLessEqual(REQUEST_TIMEOUT_SECONDS, 30)
        self.assertTrue(LocalOnlyThreadingHTTPServer.daemon_threads)

    def test_live_handler_rejects_nonlocal_host_and_cross_origin_post(self):
        server = LocalOnlyThreadingHTTPServer(("127.0.0.1", 0), OperatorHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/health", headers={"Host": "attacker.example"})
            response = connection.getresponse()
            body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 403)
            self.assertEqual(body["error"], "local_host_required")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                "/api/evaluate-case",
                body="{}",
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://attacker.example",
                },
            )
            response = connection.getresponse()
            body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 403)
            self.assertEqual(body["error"], "local_origin_required")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
