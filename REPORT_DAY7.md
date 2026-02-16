# Day7 Report (AM + Noon)

## Summary
- Collection stability: OK (0 errors, 0 missing in all runs)
- Risk: recommended departure time fluctuates heavily under fixed destination-time AM scenario.
- Under dynamic destination (now+90min), departure changes are smooth (max jump 2min).

## AM Run (07:40-08:41)
- Rows: 60, errors: 0/60
- Departure range: 07:11 ~ 07:40 (span 29 min)
- Departure jump max: 25 min
- Departure jumps >= 5 min: 6

## Noon Run (12:00-13:01) with destination=now+90min
- Rows: 60, errors: 0/60
- Departure jump max: 2 min
- Departure jumps >= 5 min: 0
- Note: departure range is large because destination-time moves forward each minute.

## Next
- Day8: simulate "fixed destination" scenario with policies (buffer/smoothing/percentile) and measure departure stability.
