# Restart Checkpoint

Current stage:
- Tableau work paused
- Switching from tiny sample data to real public-data build
- Requested scope: last 15 months ending 2026-02-28
- Truthful integrated scope adjusted because BTS currently ends at 2025-12

Project windows:
- Integrated cross-source dashboard window: 2025-01-01 to 2025-12-31
- Source-native supplemental window: 2024-12-01 to 2026-02-28 where available

Next build order:
1. Load real BTS monthly files for Jan-Dec 2025
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
