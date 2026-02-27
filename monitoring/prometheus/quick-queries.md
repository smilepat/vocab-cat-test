# Item Generation Quick Queries

아래 쿼리는 현재 구성된 메트릭(`item_generation_*`) 기준 즉시 사용 가능합니다.

## 1) 생성 채택 처리량 (5분)

```promql
sum(rate(item_generation_accepted_total{stage=~"$stage",model=~"$model",exam_type=~"$exam_type"}[5m]))
```

## 2) 생성 점수 평균 (10분)

```promql
sum(rate(item_generation_score_sum{stage=~"$stage",model=~"$model",exam_type=~"$exam_type"}[10m]))
/
clamp_min(sum(rate(item_generation_score_count{stage=~"$stage",model=~"$model",exam_type=~"$exam_type"}[10m])), 1e-9)
```

## 3) 목표-실제 난이도 오차 p90 (10분)

```promql
histogram_quantile(
  0.90,
  sum(rate(item_generation_target_gap_bucket{stage=~"$stage",model=~"$model",exam_type=~"$exam_type"}[10m])) by (le)
)
```

## 참고

- Grafana 대시보드 변수(`$stage`, `$model`, `$exam_type`)를 그대로 사용합니다.
- Prometheus Expression Browser에서는 변수를 고정 라벨(예: `stage="final"`)로 바꿔 실행하세요.
