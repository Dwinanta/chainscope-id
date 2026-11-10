from chainscope import education


def test_get_all_educational_topics_covers_core_concepts():
    topics = education.get_all_educational_topics()
    assert len(topics) >= 5
    ids = [t["id"] for t in topics]
    assert "net_worth" in ids
    assert "cash_flow" in ids
    assert "emergency_fund" in ids
    assert "asset_allocation" in ids


def test_get_topic_by_id_returns_exact_details():
    nw = education.get_topic_by_id("net_worth")
    assert nw is not None
    assert "Kekayaan Bersih" in nw["title"]
    assert "formula" in nw
