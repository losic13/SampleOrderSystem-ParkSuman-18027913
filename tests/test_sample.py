from model.sample import Sample


def test_sample_stores_all_fields():
    sample = Sample(
        sample_id="SMP-001",
        name="Wafer-A",
        avg_production_time=10.0,
        yield_rate=0.9,
        stock=5,
    )

    assert sample.sample_id == "SMP-001"
    assert sample.name == "Wafer-A"
    assert sample.avg_production_time == 10.0
    assert sample.yield_rate == 0.9
    assert sample.stock == 5


def test_sample_stock_defaults_to_zero_when_omitted():
    sample = Sample(
        sample_id="SMP-002",
        name="Wafer-B",
        avg_production_time=5.0,
        yield_rate=0.8,
    )

    assert sample.stock == 0
