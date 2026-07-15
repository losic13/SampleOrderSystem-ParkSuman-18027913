from model.sample import Sample


def _make_sample(sample_id="SMP-001", name="Wafer-A", stock=5):
    return Sample(
        sample_id=sample_id,
        name=name,
        avg_production_time=10.0,
        yield_rate=0.9,
        stock=stock,
    )


def test_add_and_get_by_id_returns_saved_sample(sample_repo):
    sample_repo.add(_make_sample())

    found = sample_repo.get_by_id("SMP-001")

    assert found == _make_sample()


def test_get_all_returns_every_saved_sample(sample_repo):
    sample_repo.add(_make_sample("SMP-001"))
    sample_repo.add(_make_sample("SMP-002"))

    all_samples = sample_repo.get_all()

    assert {s.sample_id for s in all_samples} == {"SMP-001", "SMP-002"}


def test_search_by_name_matches_case_insensitively_and_partially(sample_repo):
    sample_repo.add(_make_sample("SMP-001", name="Wafer-A"))
    sample_repo.add(_make_sample("SMP-002", name="Other"))

    found = sample_repo.search_by_name("wafer")

    assert [s.sample_id for s in found] == ["SMP-001"]


def test_update_persists_changed_fields(sample_repo):
    sample_repo.add(_make_sample())

    updated = _make_sample(stock=99)
    sample_repo.update(updated)

    assert sample_repo.get_by_id("SMP-001").stock == 99


def test_delete_removes_sample(sample_repo):
    sample_repo.add(_make_sample())

    sample_repo.delete("SMP-001")

    assert sample_repo.get_by_id("SMP-001") is None


def test_get_by_id_returns_none_when_not_found(sample_repo):
    assert sample_repo.get_by_id("NOPE") is None
