# `local_target_prior` implementation specification

Status: **recovered from the executed implementation and frozen configuration**. No method was reconstructed from model performance.

## Exact estimator

The feature groups people by the exact `addr_id` key. For a fitting sample with regional positive count $s_r$, regional sample size $n_r$, fitting-sample target mean $\mu$, and frozen smoothing strength $\alpha=20.0$,

$$
\widehat p_r=\frac{s_r+\alpha\mu}{n_r+\alpha}.
$$

There is no hierarchical geographic backoff and no minimum group-size rule. Missing `addr_id` is converted to the literal `__MISSING__` group. If that group has fitting observations it receives the same smoothed estimate; otherwise it uses the relevant fitting-sample mean.

## Leakage boundary

Training values use 5-fold deterministic out-of-fold encoding. Fold membership is the first eight bytes of `SHA256("seed|person_id")`, interpreted as a little-endian integer modulo 5; the canonical seed is 42. A training row's label and every label in its held-out fold are excluded from that row's encoded value. A region unseen outside the held-out fold falls back to the out-of-fold mean $\mu_{-f}$.

After producing all training OOF values, the encoder is fitted once on the complete training partition. Validation and test transformations accept region keys only and never accept their labels. An unseen `addr_id` falls back to the complete-training target mean.

## Population and shift behavior

The dataset is filtered to Global, Song, or Ming before the split is materialized, so each population receives a separate encoder. Primary, matched-random, and matched-spatial runs each refit the encoder from that protocol's training partition; mappings are not shared across protocols. Under matched-spatial shift, an `addr_id` absent from spatial training therefore receives that population/protocol training mean.

## Provenance

- Implementation: `src/geography.py:FoldSafeLocalEntryEncoder`
- Executed caller: `src/phase26.py:prepare_phase26_data`
- Frozen configuration: `configs/phase2_6_features.yaml`
- Unsupported additions explicitly absent: hierarchical pooling, minimum-count pooling, coordinate-nearest backoff, and external priors.
