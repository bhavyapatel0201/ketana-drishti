from datetime import datetime

from ketana_drishti.chart import build_chart


def test_chart_has_core_fields():
    data = build_chart(datetime(1998, 5, 14, 8, 30), lat=23.0225, lon=72.5714)
    assert data["_input"]["timezone"] == "Asia/Kolkata"
    assert data["_input"]["utc_offset_hours"] == 5.5
    assert len(str(data)) > 500
