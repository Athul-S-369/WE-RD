from weird.security import is_safe_http_url, sanitize_html


def test_sanitize_strips_scripts():
    dirty = '<p>ok</p><script>alert(1)</script><a href="https://example.com">x</a>'
    clean = sanitize_html(dirty)
    assert "<script>" not in clean
    assert "ok" in clean
    assert 'href="https://example.com"' in clean


def test_url_guard():
    assert is_safe_http_url("https://example.com/a")
    assert is_safe_http_url("http://example.com/a")
    assert not is_safe_http_url("javascript:alert(1)")
    assert not is_safe_http_url("file:///etc/passwd")
