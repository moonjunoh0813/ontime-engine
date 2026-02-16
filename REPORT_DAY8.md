# Day8 Report (Recompute from Log)

## What we did
- Recomputed recommended departure times using stored ETA snapshots (offline simulation).
- Goal: measure stability without re-collecting data, enabling policy iteration.

## AM (fixed destination-time style)
- Departure range span: 29 min
- Departure jump max: 29 min
- Departure jumps >= 5 min: 10
- Verdict: high volatility under fixed destination time.

## Noon (destination = now + 90 min)
- Departure span is large because destination moves forward each minute (not a stability metric).
- Slack (departure - now): min=31, max=31, avg=31 (constant across 60 samples)
- Verdict: very stable under relative destination time; always “now < recommended departure”.

## Conclusion
- Relative-destination mode is stable.
- Fixed-destination mode remains risky without additional policy/model changes.
- Next: Day9 decision should consider pivoting UX/policy or improving ETA modeling (multi-vehicle, segment learning, smoothing).
