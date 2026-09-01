"""Collection-only CatBoost import guard for non-experimental release tests.

The frozen test suite imports ``src.phase26`` to inspect feature policies. The
release environment used for the final paper audit does not install CatBoost,
and Phase 3.1.1 must not instantiate a trainer. Putting this directory first on
``PYTHONPATH`` lets policy and artifact tests collect without enabling training.
"""


class CatBoostClassifier:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("CatBoost training is disabled in the Phase 3.1.1 non-experimental test guard")
