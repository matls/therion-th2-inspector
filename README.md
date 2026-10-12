# Therion TH2 Inspector (vývojová verze 4)

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

## Automatické sloučení – omezení

Pro první bezpečnou verzi lze schválit pouze dvě bezprostředně sousedící definice `line`, bez `-id`, bez vnitřních direktiv, se shodnou hlavičkou a bez rozvětvení v místě napojení. V ostatních případech se návrh pouze zobrazí. V této verzi se hledá orientace konec → začátek; opačné orientace zatím ne.

Nástroj nepřepočítává Bézierovy řídicí body. Při sloučení odstraní pouze společný duplicitní bod, první `endline` a druhou hlavičku `line`; tím zachová geometrii segmentů. Všechny změny se provádějí po explicitním schválení.

## Zálohování

Před zápisem do originálů vznikne `_Therion_zalohy/<čas>/` s kopií **jen měněných souborů** a `protokol.json`. Při kontrole se ignorují všechny podsložky `Data` (bez ohledu na velikost písmen) a `_Therion_zalohy`.

## Důležité

Jde o vývojovou verzi: první dávku oprav ověř na kopii projektu a porovnej export Therionu. Nástroj nevyhodnocuje všechny konstrukce `.th2` a nezaručuje, že sloučení zachová význam odkazů mimo kontrolovaný soubor. U čar s ID automatické sloučení není povoleno.

## Další vývoj

Doporučené úkoly: slučování vzdálených definic, obrácená orientace čar, detekce referencí na ID a rychlejší prostorový index pro rozsáhlé scrappy.

## Verze 4

- Přesně navazující čáry se stejnou hlavičkou lze schválit ke sloučení i tehdy, pokud jsou v souboru vzdálené nebo zapsané v opačném pořadí než geometrická návaznost. Podporovány jsou interní direktivy `smooth on/off`; `-id` a ostatní interní direktivy stále blokují automatické sloučení.
- Po sobě jdoucí stejný koncový bod lze odstranit i jako celý Bézierův segment se šesti souřadnicemi, pokud řídicí body leží nejvýše 30 jednotek od společného bodu. **Tím se úmyslně odstraní nakreslená smyčka.** Větší smyčky zůstávají jen ke kontrole.
- Opravy se provádějí až po schválení a zálohování měněných originálů. Před použitím na hlavním projektu zkontroluj výsledek v Therionu.
- Testy: `python -m unittest discover -s tests -v`.
