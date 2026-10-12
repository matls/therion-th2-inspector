# Therion TH2 Inspector (vývojová verze 5)

Lokální nástroj pro kontrolu `.th2` kresby v prohlížeči. Vyžaduje Python 3.9+; nepoužívá externí balíčky. Není oficiálním projektem Therionu.

## Windows

Rozbal ZIP a spusť `SPUSTIT_KONTROLU.bat`; případně:

```bat
py therion_kontrola.py "D:\Jeskyne" --near 1.0
```

Otevře se lokální web na `127.0.0.1` (bez přístupu z internetu). Procházej nálezy, schval změny, klikni na **Zobrazit plán změn** a až pak na **Zálohovat a provést schválené změny**.

## Co se kontroluje

- Samoprotínání uvnitř jednoho Bézierova segmentu (numerické přiblížení).
- Duplicitní koncové body jedné čáry; `-close on` toleruje shodu prvního a posledního bodu.
- `chimney`, `pit`, `border`, `rock-border`: chybějící `-close on`, **jen pokud první a poslední bod mají přesně stejné souřadnice**.
- `merge`: přesná návaznost konec A → začátek B v jednom scrapu, shodný typ a všechny parametry v hlavičce.
- `near`: návaznost s malou odchylkou (výchozí 1 souřadnicová jednotka, lze nastavit `--near`); **pouze upozornění**.

## Sloučení čar – pouze ruční návrhy

Nástroj zobrazuje přesně navazující čáry a blízké koncové body. **V této verzi žádné sloučení neprovádí**, a to ani přes API. Při ručním sloučení zkontroluj směrové parametry jako `-reverse`, direktivy `smooth` a případné reference na ID. Návrhy hledají primárně konec → začátek; nejde o úplný analyzátor všech variant orientace.

## Zálohování

Před zápisem do originálů vznikne `_Therion_zalohy/<čas>/` s kopií **jen měněných souborů** a `protokol.json`. Při kontrole se ignorují všechny podsložky `Data` (bez ohledu na velikost písmen) a `_Therion_zalohy`.

## Důležité

Jde o vývojovou verzi: první dávku oprav ověř na kopii projektu a porovnej export Therionu. Nástroj nevyhodnocuje všechny konstrukce `.th2` a nezaručuje správnost všech automatických oprav pro libovolný soubor. Sloučení čar je vždy ruční.

## Další vývoj

Doporučené úkoly: slučování vzdálených definic, obrácená orientace čar, detekce referencí na ID a rychlejší prostorový index pro rozsáhlé scrappy.

## Verze 4

- Přesně navazující čáry se stejnou hlavičkou lze schválit ke sloučení i tehdy, pokud jsou v souboru vzdálené nebo zapsané v opačném pořadí než geometrická návaznost. Podporovány jsou interní direktivy `smooth on/off`; `-id` a ostatní interní direktivy stále blokují automatické sloučení.
- Po sobě jdoucí stejný koncový bod lze odstranit i jako celý Bézierův segment se šesti souřadnicemi, pokud řídicí body leží nejvýše 30 jednotek od společného bodu. **Tím se úmyslně odstraní nakreslená smyčka.** Větší smyčky zůstávají jen ke kontrole.
- Opravy se provádějí až po schválení a zálohování měněných originálů. Před použitím na hlavním projektu zkontroluj výsledek v Therionu.
- Testy: `python -m unittest discover -s tests -v`.

## Verze 5 – sloučení pouze ručně

- Přesné návaznosti a blízké konce se nadále vyhledávají a vykreslují, ale **nelze schválit automatické sloučení**.
- Server odmítne požadavek na sloučení i při přímém volání API; grafické tlačítko je deaktivované.
- Opravy duplicitních bodů, malých Bézierových smyček a `-close on` zůstávají dostupné se zálohováním.
- Směrové atributy jako `-reverse` musí při ručním sloučení zkontrolovat člověk.
