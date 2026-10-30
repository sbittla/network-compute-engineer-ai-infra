# Postmortem {{incident_id}} - {{title}}

Status: draft | Severity: {{severity}} | Blameless: yes | Owner: {{owner}}

## Summary
{{summary}}

## Impact
- Affected workloads: {{affected_jobs}}
- Duration of user-visible impact (onset to mitigation): {{impact_minutes}} min
- Lost accelerator time [MODELED from step records]: {{lost_gpu_hours}} GPU-hours
- Training throughput SLI during the 6-hour window: {{training_sli}}
- Inference SLOs: {{inference_impact}}

## Timeline (UTC)
{{timeline}}

## Detection
- Time to detect (onset to first human/alert signal): {{ttd_min}} min
- How detected: {{how_detected}}
- Alerting gap (missing alert): {{missing_alert}}
- Noisy alert that should be redesigned: {{noisy_alert}}

## Root cause and trigger
{{root_cause}}

## Rejected hypotheses (and the evidence that rejected them)
{{rejected_hypotheses}}

## What went well / what went poorly / where we got lucky
{{went_well}}

## Action items (owner, priority, due)
{{action_items}}
