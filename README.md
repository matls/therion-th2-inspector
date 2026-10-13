# Therion TH2 Inspector – verze 12 (experimentální)

Lokální Python/HTML nástroj pro hledání a schvalování oprav souborů `.th2`. Nejde o oficiální součást Therionu.

## Spuštění ve Windows

1. Rozbal ZIP.
2. Spusť `SPUSTIT_KONTROLU.bat` a zadej cestu ke složce mapy.
3. V prohlížeči zkontroluj navržené opravy; teprve po kontrole použij **Zálohovat a provést schválené změny**.

Ruční spuštění: `py therion_kontrola.py "C:\mapy\jeskyne" --near 1.0`. Přepínač `--near` určuje maximální vzdálenost navazujících konců v souřadnicových jednotkách TH2; pro vyšší bezpečnost používej nízkou toleranci.

## Funkce a pravidla sloučení

- **Přesné návaznosti i blízké konce:** schválení spojení dvou čar a celých řetězců. Při blízkých koncích vznikne společný bod v souřadnicích **konce předchozí čáry**; počáteční bod navazující čáry se přizpůsobí. Ostatní souřadnice a Bézierovy řídicí body se nepřepočítávají. Zelený přerušovaný náhled ukazuje změnu prvního úseku připojované čáry.
- **Shodné parametry:** podporujeme i identické `-reverse on/off`, `-subtype` a další parametry hlavičky; pořadí parametrů v hlavičce se může lišit. Parametry musí být shodné u všech členů řetězce. Nejednoznačné nebo opakované parametry jsou pouze ke kontrole.
- **Směr spojení:** přímé sloučení vyžaduje návaznost konec A → začátek B. Pro vybrané čáry s `-reverse on` je dostupné samostatně schvalované obrácení geometrie; následně znovu prohledej projekt a spoj čáry. Čáry bez explicitního `-reverse on` se neobracejí. Čáry s `-id`, komentáři uvnitř těla, uzavřené čáry, rozvětvení a nejednoznačné kombinace se automaticky neslučují. Vnitřní `smooth on/off` a bodový atribut `altitude` jsou podporovány a zachovávají se na původním místě. `smooth` navázané na počáteční bod připojované čáry zůstává jen ke kontrole; jiné vnitřní direktivy rovněž.
- **Uzavření:** je-li první a poslední bod jedné `line` přesně stejný a chybí `-close on`, nabídne se změna na `-close on` i pro `wall`; totožnost prvního a posledního bodu se nezobrazuje jako smazatelná duplicita. Jinak zůstávají opravy duplicitních přímých bodů a drobných Bézierových smyček.
- **Vyloučené složky:** `data`, `záloha`, `zaloha` a `_Therion_zalohy` v jakékoli úrovni, bez ohledu na velikost písmen. Seznam je viditelný v záhlaví stránky.

## Další kontroly

Samoprotínání Bézierových segmentů: návrh úpravy řídicích bodů s náhledem červená/zelená. Filtr podle druhu nálezu, opravitelnosti a stavu schválení. Nástroj odmítá souběžně schválená konfliktní sloučení. U více navazujících čar nabízí sloučení celého řetězce.

## Zálohování a bezpečnost

Před úpravou se do `_Therion_zalohy/<čas>/` uloží kopie **pouze souborů, které se skutečně upravují**, a `protokol.json`. Soubory změněné od posledního skenování jsou odmítnuty. Úpravy křivek a spojování nepatrně vzdálených konců **mění geometrii** a jejich vhodnost pro skutečnou mapu musí schválit člověk. Nejdříve vyzkoušej kopii mapového projektu a ověř výstup v Therionu.

## Testy

`py -m unittest discover -s tests -v`

41 automatických testů pokrývá mimo jiné totožné i různě seřazené `-reverse`/`-subtype`, přesnou a blízkou návaznost včetně Bézierovy křivky, smíšené řetězce, konflikty, zachované `smooth on/off` i blokované rizikové vnitřní direktivy, uzavření `wall`, zálohy a vyloučené složky. JavaScript byl zkontrolován pomocí `node --check`.

Zdrojový kód: https://github.com/matls/therion-th2-inspector

## Úprava rozhraní (13. 10. 2026)
Záhlaví je kompaktní, informace o projektu a vynechaných složkách jsou vedle názvu. Výška seznamu a náhledu se přizpůsobuje prostoru.

## Verze 9: proč sloučení nejde

Nálezy přesné i blízké návaznosti zobrazují **v horní části detailu všechny konkrétní překážky**: rozdílné hodnoty pojmenovaných atributů (včetně `-reverse` a `-subtype`), existující `-id`, direktivy nebo komentáře uvnitř čáry s čísly řádků, rozvětvení a konfliktní návrhy. Bezpečnostní podmínky pro automatické provádění oprav zůstaly stejné jako ve verzi 8. Jednořádkové záhlaví zůstává zachované.

## Verze 10: `smooth` a odkazy na ID

- Vnitřní `smooth on/off` u bodů uvnitř čáry ani na konci první čáry automatické sloučení neblokují. Jejich řádky zůstanou zachované vůči geometrii. `smooth` u prvního bodu následující čáry je blokováno, aby nedošlo k nepřesnému přesunu direktivy do spoje.
- Soubor s ID zůstává pouze k ručnímu posouzení. U návrhů s ID nástroj prohledá `.th` a `.th2` v kořenové složce a podadresářích (mimo vyloučené složky) a vypíše místa se stejným tokenem. Nejde o úplný parser Therionu: nerozpozná všechny složené / kvalifikované reference, kontextové vazby či importy mimo kořen projektu. Nenalezení výskytu neopravňuje ID smazat.
- K žádným externím souborům mimo vybraný kořen se přístup neprovádí.

**Zálohy před opravami zůstávají zachované.** První použití vyzkoušej na kopii projektu.

## Verze 11: bezpečné obrácení geometrie `-reverse on`

- Samostatný typ nálezu **Obrácení -reverse on**, individuální schválení, automatická záloha. Jen `wall`, `slope`, `pit`, `chimney`, `floor-step`; nikoli `border` nebo čáry bez `-reverse on`.
- Otočí pořadí bodů a Bézierových segmentů, včetně prohození dvojice řídicích bodů; odstraní `-reverse on` z hlavičky. Verifikace všech přímých i Bézierových segmentů porovnává souřadnice bez zaokrouhlení. Vnitřní `smooth on/off` se přemístí s původním bodem.
- Čáry s ID, uzavřené čáry, neznámé direktivy a `smooth` na krajním bodu se **automaticky neobracejí**. `smooth` na krajním bodu má při obrácení nejednoznačný význam.
- Po schválení obrácení spusť nové prohledání: následně se mohou zobrazit další návrhy sloučení. Obrácení a slučování se provádí **ve dvou samostatných dávkách**; stejné čáry nelze ve stejné dávce obracet a upravovat jinak.
- Pro některé směrové atributy může být výsledek významově citlivý; ověř zobrazení a výsledek kompilace v Therionu na kopii projektu.

## Verze 12: bodový atribut `altitude`

- `altitude` u bodů `line` se zachová spolu s příslušným bodem při obrácení čáry s `-reverse on` (i u krajních bodů). Zachová se původní text hodnoty, včetně hodnot v hranatých závorkách.
- Při sloučení se zachovají atributy `altitude` u všech bodů. `altitude` z odstraněného prvního bodu navazující čáry se přenese na společný bod. Při dvou shodných hodnotách se zachová jen jeden výskyt.
- Rozdílné hodnoty `altitude` ve společném bodu se automaticky neslučují. Pokud má počáteční bod navazující čáry `altitude` a konce jsou jen blízko (nikoli identické), sloučení se zablokuje. `smooth` na začátku připojované čáry zůstává pouze ke kontrole.
- Jiné neznámé vnitřní direktivy stále blokují automatický zásah. Obracení čar s ID a typu `border` zůstává zakázané.
- Přibylo sedm regresních testů pro atributy na krajních i vnitřních bodech, kombinaci se `smooth`, slučování a konflikt výšek.
