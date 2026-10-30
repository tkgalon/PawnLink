from pawnlink.training.promote import gate

CHAMPION = {"test_auc": 0.987, "test_recall": 0.980, "legit_paths_fpr": 0.70}


def _passed(**candidate):
    return [ok for _, ok in gate(CHAMPION | candidate, CHAMPION)]


def test_better_on_legit_paths_with_small_auc_cost_passes():
    assert all(_passed(test_auc=0.984, test_recall=0.975, legit_paths_fpr=0.10))


def test_large_auc_drop_fails():
    assert not all(_passed(test_auc=0.97, legit_paths_fpr=0.10))


def test_recall_drop_fails():
    assert not all(_passed(test_recall=0.95, legit_paths_fpr=0.10))


def test_no_improvement_on_legit_paths_fails():
    assert not all(_passed(legit_paths_fpr=0.70))
