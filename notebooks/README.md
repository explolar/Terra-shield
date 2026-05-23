# Notebooks — research & validation track

These notebooks back the platform with reproducible science and feed the
publication targets in [`../docs/roadmap.md`](../docs/roadmap.md). They import the
same `terrashield_geo` package the API uses, so what you validate is what ships.

## Planned notebooks

| Notebook | Purpose | Feeds |
|----------|---------|-------|
| `01_flood_susceptibility_ahp.ipynb` | AHP weight derivation + consistency, weighted-overlay susceptibility for an Indian basin; validate vs. historical flood footprints | FloodAI paper |
| `02_sar_flood_unet.ipynb` | Sentinel-1 SAR flood segmentation (Otsu baseline → U-Net on Sen1Floods11); report IoU/F1 | FloodAI paper |
| `03_climate_cmip6_ssp.ipynb` | NEX-GDDP-CMIP6 district projections, extreme indices (R95p, heatwave days), SSP245 vs SSP585 | ClimateLens × WRF paper |
| `04_drought_spi_validation.ipynb` | SPI gamma-fit vs. z-score approximation; compare to declared drought years | DroughtAI |
| `05_resilience_or.ipynb` | Shelter siting (MCLP) and evacuation routing case study; greedy vs. ILP optimum | ResilienceOR note |

## Conventions

- Use **spatial cross-validation** for any predictive model — never random K-fold
  (see [`../docs/engineering.md`](../docs/engineering.md) §2).
- Report the **Area of Applicability** with every map.
- Keep large rasters/outputs out of git (see `.gitignore`).
