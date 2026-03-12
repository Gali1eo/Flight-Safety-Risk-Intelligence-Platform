# Architecture Overview

## Design Principles
- Use only public or synthetic data.
- Keep raw, trusted, and analytics layers separate.
- Standardize columns to snake_case.
- Apply basic null, duplicate, and schema validation before promoting data.
- Avoid exposing identifiers or sensitive narrative text in downstream outputs.

## Pipeline Flow
1. Ingestion modules load approved source data into the raw layer.
2. Transformation modules clean and standardize source-aligned records into trusted tables.
3. Feature modules derive analytical and modeling features from trusted tables.
4. Model modules train starter risk models and publish summary metrics.
5. SQL marts reshape analytics outputs for dashboard and reporting consumption.

## Privacy Posture
- Narrative-heavy datasets are treated as sensitive even when public.
- Downstream analytics tables should prefer aggregate counts, rates, and engineered flags.
- Access should follow least-privilege principles by audience and use case.

## Extensibility
- Additional source-specific adapters can be added under `src/ingest`.
- Statistical validation in R can be connected to `data/analytics`.
- Tableau extracts can be generated directly from marts or analytics tables.
