# Restart Checkpoint

Current stage:
- Jan-Feb 2025 real-data pilot prep in progress
- Tableau work remains paused for the pilot rebuild
- FAASTeam manual extraction deferred for this pilot
- Synthetic safety culture remains in place for the pilot

Pilot window:
- Integrated pilot scope: 2025-01-01 to 2025-02-28

Next build order:
1. Use real BTS Jan-Feb 2025 monthly CSV files already placed in `data/raw/bts_on_time`
2. Use the real NASA ASRS Jan-Feb 2025 export already placed in `data/raw/nasa_asrs`
3. Extract an official NTSB Jan-Feb 2025 CSV intermediate from the MDB source and place it in `data/raw/ntsb_investigations`
4. Rebuild trusted layer
5. Rebuild analytics marts
6. Validate Jan-Feb 2025 outputs
7. Resume Tableau work only after the pilot marts look correct

Important constraints:
- Public or synthetic data only
- No FOQA, ASAP, or internal SMS claims
- Aggregate-only joins
- Do not touch Tableau files during pilot adapter updates
