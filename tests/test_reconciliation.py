from qlrk.reconciliation import Fill, reconcile


def _f(oid, sym="X", side="BUY", qty=10, price=100.0, ts="2026-01-01T14:00:00+00:00"):
    return Fill(order_id=oid, symbol=sym, side=side, qty=qty, price=price, ts=ts)


def test_identical_fills_match_cleanly():
    m = [_f("1"), _f("2")]
    b = [_f("1"), _f("2")]
    report = reconcile(m, b)
    assert report.clean
    assert report.matched == 2


def test_missing_at_broker_detected():
    report = reconcile([_f("1"), _f("2")], [_f("1")])
    assert not report.clean
    kinds = {d.kind for d in report.divergences}
    assert "missing_at_broker" in kinds


def test_extra_at_broker_detected():
    report = reconcile([_f("1")], [_f("1"), _f("2")])
    assert not report.clean
    kinds = {d.kind for d in report.divergences}
    assert "extra_at_broker" in kinds


def test_price_mismatch_outside_tolerance():
    m = [_f("1", price=100.00)]
    b = [_f("1", price=100.05)]
    report = reconcile(m, b, price_tolerance=0.01)
    kinds = {d.kind for d in report.divergences}
    assert "price_mismatch" in kinds


def test_price_within_tolerance_matches():
    m = [_f("1", price=100.00)]
    b = [_f("1", price=100.005)]
    report = reconcile(m, b, price_tolerance=0.01)
    assert report.clean


def test_qty_mismatch():
    report = reconcile([_f("1", qty=10)], [_f("1", qty=9)])
    kinds = {d.kind for d in report.divergences}
    assert "qty_mismatch" in kinds


def test_side_mismatch():
    report = reconcile([_f("1", side="BUY")], [_f("1", side="SELL")])
    kinds = {d.kind for d in report.divergences}
    assert "side_mismatch" in kinds


def test_accepts_dicts():
    m = [{"order_id": "1", "symbol": "X", "side": "BUY", "qty": 1, "price": 1.0, "ts": "t"}]
    b = [{"order_id": "1", "symbol": "X", "side": "BUY", "qty": 1, "price": 1.0, "ts": "t"}]
    report = reconcile(m, b)
    assert report.clean


def test_report_dict_shape():
    report = reconcile([_f("1", price=1.0)], [_f("1", price=5.0)])
    d = report.to_dict()
    assert "matched" in d and "divergences" in d and "clean" in d
    assert d["clean"] is False
    assert d["divergences"][0]["kind"] == "price_mismatch"
