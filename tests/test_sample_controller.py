def test_register_persists_sample_with_given_fields(sample_controller):
    sample = sample_controller.register(
        sample_id="SMP-001",
        name="Wafer-A",
        avg_production_time=10.0,
        yield_rate=0.9,
        stock=5,
    )

    assert sample.sample_id == "SMP-001"
    assert sample_controller.list_all() == [sample]


def test_search_by_name_delegates_to_repository(sample_controller):
    sample_controller.register(
        sample_id="SMP-001", name="Wafer-A", avg_production_time=10.0, yield_rate=0.9,
    )
    sample_controller.register(
        sample_id="SMP-002", name="Other", avg_production_time=10.0, yield_rate=0.9,
    )

    found = sample_controller.search_by_name("wafer")

    assert [s.sample_id for s in found] == ["SMP-001"]
