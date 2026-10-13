# Změny Therion TH2 Inspector

## v11
- Individuálně schvalované obrácení geometrie pro `wall`, `slope`, `pit`, `chimney`, `floor-step` s explicitním `-reverse on`.
- Přesné obrácení Bézierových segmentů; validace stejných souřadnic a přesunu vnitřních `smooth`.
- Chráněno ID, `border`, čáry bez `-reverse on`, uzavřené a nejednoznačné čáry.
- Dvoufázové slučování: nejprve obrátit, pak znovu skenovat a schválit spojení.
- 34 automatických testů.

## v10
- Podpora interního `smooth on/off` při sloučení a diagnostika odkazů na ID.

## v9
- Podrobné důvody blokování sloučení.
