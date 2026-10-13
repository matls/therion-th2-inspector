# Změny Therion TH2 Inspector

## v12
- Bodové `altitude` se přenáší s bodem při přesném obrácení geometrie; zachovává se i u krajních bodů.
- Sloučení bezpečně zachovává altitude na společném bodu, odmítá rozdílné výšky a neurčitou blízkou návaznost s výškou.
- 41 automatických testů.

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
