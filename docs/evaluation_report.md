# Evaluation Report

Rows: 30

## Metrics

- **accuracy:** `0.5`
- **macro_precision:** `0.5808`
- **macro_recall:** `0.4906`
- **macro_f1:** `0.4873`
- **weighted_f1:** `0.4884`
- **per_class_accuracy:** `{'notify': 0.4444, 'digest': 0.7273, 'mute': 0.3}`
- **mean_confidence:** `0.7087`
- **ece:** `0.2087`
- **brier_score:** `0.2864`
- **calibration_gap:** `0.2087`
- **evidence_precision:** `0.0`
- **evidence_recall:** `0.0`
- **action_distribution:** `{'digest': 19, 'mute': 4, 'notify': 7}`

## Confusion matrix

```text
expected\predicted | notify | digest | mute
-------------------|--------|--------|-----
notify             | 4 | 5 | 0
digest             | 2 | 8 | 1
mute               | 1 | 6 | 3
```

## Calibration

The reliability diagram is written to `evaluation_plots/reliability.svg`; the report does not claim calibration quality when labels are absent.
