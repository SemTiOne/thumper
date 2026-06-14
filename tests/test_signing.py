from thumper.services import signing


def test_sign_timestamped_binds_timestamp_and_body():
    sig_a = signing.sign_timestamped("secret", 1000, b'{"x":1}')
    sig_b = signing.sign_timestamped("secret", 1001, b'{"x":1}')
    # Same body, different ts -> different signature (timestamp is bound in).
    assert sig_a != sig_b
    assert sig_a.startswith("sha256=")


def test_verify_timestamped_accepts_fresh_valid():
    body = b'{"hello":"world"}'
    sig = signing.sign_timestamped("secret", 1000, body)
    assert signing.verify_timestamped("secret", 1000, body, sig, now=1100) is True


def test_verify_timestamped_rejects_stale():
    body = b'{"hello":"world"}'
    sig = signing.sign_timestamped("secret", 1000, body)
    # 1000 + 301 > max_age 300 -> stale
    assert signing.verify_timestamped("secret", 1000, body, sig, now=1301) is False


def test_verify_timestamped_rejects_bad_signature():
    body = b'{"hello":"world"}'
    assert signing.verify_timestamped("secret", 1000, body, "sha256=deadbeef", now=1000) is False


def test_verify_timestamped_rejects_missing_signature():
    assert signing.verify_timestamped("secret", 1000, b"x", None, now=1000) is False


def test_verify_timestamped_accepts_exact_window_edge():
    body = b'{"hello":"world"}'
    sig = signing.sign_timestamped("secret", 1000, body)
    # exactly max_age (300s) away -> still accepted (strict > comparison)
    assert signing.verify_timestamped("secret", 1000, body, sig, now=1300) is True


def test_verify_timestamped_rejects_future_skew():
    body = b"x"
    sig = signing.sign_timestamped("secret", 2000, body)
    # ts far in the future relative to now -> beyond forward skew cap -> reject
    assert signing.verify_timestamped("secret", 2000, body, sig, now=1000) is False


def test_verify_timestamped_allows_small_forward_drift():
    body = b"x"
    sig = signing.sign_timestamped("secret", 1060, body)
    # 60s ahead == max_skew edge -> accepted (absorbs clock drift)
    assert signing.verify_timestamped("secret", 1060, body, sig, now=1000) is True


def test_verify_timestamped_rejects_modest_future_ts():
    body = b"x"
    sig = signing.sign_timestamped("secret", 1120, body)
    # 120s ahead: inside the old symmetric +/-300 window, but past the 60s forward
    # cap -> rejected, so an attacker can't future-date a ts to stretch the window.
    assert signing.verify_timestamped("secret", 1120, body, sig, now=1000) is False
