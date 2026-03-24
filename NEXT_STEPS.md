# Restart Checkpoint

Current stage:
- Tableau work paused
- Switching from tiny sample data to real public-data build
- Requested scope: last 15 months ending 2026-02-28
- Truthful integrated scope adjusted because official BTS Reporting Carrier On-Time data currently appear to end at 2025-11 as of 2026-03-24

Project windows:
- Planned integrated cross-source dashboard window: 2025-01-01 to 2025-12-31
- Current executable integrated dashboard window: 2025-01-01 to 2025-11-30
- Source-native supplemental window: 2024-12-01 to 2026-02-28 where available

Next build order:
1. Load real BTS monthly files for Jan-Nov 2025 and verify whether Dec 2025 has been officially released
2. Load real NASA ASRS exports for Dec 2024-Feb 2026 if query results support it
3. Load real NTSB aviation investigation data for Dec 2024-Feb 2026
4. Load real FAASTeam past events for the last 15 months
5. Rebuild trusted layer
6. Rebuild analytics marts
7. Rebuild Dashboard 1 in Tableau using real data

Important constraints:
- Public or synthetic data only
- No FOQA, ASAP, or internal SMS claims
- Aggregate-only joins
- Use `docs/real_data_acquisition_checklist.md` as the real-data acquisition and rebuild runbook
