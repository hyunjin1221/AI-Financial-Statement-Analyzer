from app.services.llm_engine import _extract_json_block, _normalize_payload, attach_evidence_spans, merge_insights


def test_extract_json_block_handles_wrapped_text() -> None:
    text = "Here is output:\n{\"revenue_trends\":[\"Revenue up\"],\"confidence\":0.8}\nThanks"
    payload = _extract_json_block(text)
    assert payload["revenue_trends"] == ["Revenue up"]
    assert payload["confidence"] == 0.8


def test_normalize_payload_enforces_schema() -> None:
    payload = _normalize_payload({"revenue_trends": "bad_type", "confidence": "1.2"})
    assert payload["revenue_trends"] == []
    assert payload["confidence"] == 1.0
    assert isinstance(payload["red_flags"], list)


def test_merge_insights_dedupes_and_averages_confidence() -> None:
    merged = merge_insights(
        [
            {
                "revenue_trends": ["Revenue growth in cloud"],
                "red_flags": ["Customer concentration"],
                "confidence": 0.7,
            },
            {
                "revenue_trends": ["Revenue growth in cloud", "Margin pressure in hardware"],
                "red_flags": ["Customer concentration", "Debt maturity in 2027"],
                "confidence": 0.5,
            },
        ]
    )
    assert merged["revenue_trends"] == ["Revenue growth in cloud", "Margin pressure in hardware"]
    assert merged["red_flags"] == ["Customer concentration", "Debt maturity in 2027"]
    assert abs(merged["confidence"] - 0.6) < 1e-9


def test_attach_evidence_spans_maps_quotes_to_sections() -> None:
    insights = {"evidence_quotes": ["Debt covenants may restrict flexibility."]}
    section_records = {
        "risk_factors": {
            "text": "Item 1A Risk Factors Debt covenants may restrict flexibility.",
            "start": 120,
            "end": 180,
        }
    }
    enriched = attach_evidence_spans(insights, section_records)
    assert enriched["evidence_spans"][0]["section"] == "risk_factors"
    assert enriched["evidence_spans"][0]["start"] is not None
