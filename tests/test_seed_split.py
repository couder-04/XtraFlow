from sim.util import load_config, seed_range


def test_seed_ranges_disjoint():
    cfg = load_config()
    train = set(seed_range(cfg["seed_protocol"]["train"]))
    val = set(seed_range(cfg["seed_protocol"]["validation"]))
    test = set(seed_range(cfg["seed_protocol"]["test"]))
    assert train.isdisjoint(val)
    assert train.isdisjoint(test)
    assert val.isdisjoint(test)
    assert min(train) == 1000 and max(train) == 1049
    assert min(val) == 2000 and max(val) == 2019
    assert min(test) == 1 and max(test) == 30


def test_config_lock_roundtrip(tmp_path):
    from sim.util import assert_config_locked, config_sha256, freeze_config, ROOT
    h = freeze_config()
    assert h == config_sha256()
    assert_config_locked()
