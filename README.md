# Therion TH2 Inspector – verze 10 (experimentální)

Lokální Python/HTML nástroj pro hledání a schvalování oprav souborů `.th2`. Nejde o oficiální součást Therionu.

## Spuštění ve Windows

1. Rozbal ZIP.
2. Spusť `SPUSTIT_KONTROLU.bat` a zadej cestu ke složce mapy.
3. V prohlížeči zkontroluj navržené opravy; teprve po kontrole použij **Zálohovat a provést schválené změny**.

Ruční spuštění: `py therion_kontrola.py "C:\mapy\jeskyne" --near 1.0`. Přepínač `--near` určuje maximální vzdálenost navazujících konců v souřadnicových jednotkách TH2; pro vyšší bezpečnost používej nízkou toleranci.

## Funkce a pravidla sloučení

- **Přesné návaznosti i blízké konce:** schválení spojení dvou čar a celých řetězců. Při blízkých koncích vznikne společný bod v souřadnicích **konce předchozí čáry**; počáteční bod navazující čáry se přizpůsobí. Ostatní souřadnice a Bézierovy řídicí body se nepřepočítávají. Zelený přerušovaný náhled ukazuje změnu prvního úseku připojované čáry.
- **Shodné parametry:** podporujeme i identické `-reverse on/off`, `-subtype` a další parametry hlavičky; pořadí parametrů v hlavičce se může lišit. Parametry musí být shodné u všech členů řetězce. Nejednoznačné nebo opakované parametry jsou pouze ke kontrole.
- **Směr spojení:** jen geometrická návaznost konec A → začátek B. Nesnažíme se obracet geometrii ani měnit `-reverse`. Čáry s `-id`, komentáři uvnitř těla, uzavřené čáry, rozvětvení a nejednoznačné kombinace se automaticky neslučují. Vnitřní `smooth on` a `smooth off` jsou nově podporovány a zachovávají se na původním místě. `smooth` navázané na počáteční bod připojované čáry zůstává jen ke kontrole; jiné vnitřní direktivy rovněž.
- **Uzavření:** je-li první a poslední bod jedné `line` přesně stejný a chybí `-close on`, nabídne se změna na `-close on` i pro `wall`; totožnost prvního a posledního bodu se nezobrazuje jako smazatelná duplicita. Jinak zůstávají opravy duplicitních přímých bodů a drobných Bézierových smyček.
- **Vyloučené složky:** `data`, `záloha`, `zaloha` a `_Therion_zalohy` v jakékoli úrovni, bez ohledu na velikost písmen. Seznam je viditelný v záhlaví stránky.

## Další kontroly

Samoprotínání Bézierových segmentů: návrh úpravy řídicích bodů s náhledem červená/zelená. Filtr podle druhu nálezu, opravitelnosti a stavu schválení. Nástroj odmítá souběžně schválená konfliktní sloučení. U více navazujících čar nabízí sloučení celého řetězce.

## Zálohování a bezpečnost

Před úpravou se do `_Therion_zalohy/<čas>/` uloží kopie **pouze souborů, které se skutečně upravují**, a `protokol.json`. Soubory změněné od posledního skenování jsou odmítnuty. Úpravy křivek a spojování nepatrně vzdálených konců **mění geometrii** a jejich vhodnost pro skutečnou mapu musí schválit člověk. Nejdříve vyzkoušej kopii mapového projektu a ověř výstup v Therionu.

## Testy

`py -m unittest discover -s tests -v`

28 automatických testů pokrývá mimo jiné totožné i různě seřazené `-reverse`/`-subtype`, přesnou a blízkou návaznost včetně Bézierovy křivky, smíšené řetězce, konflikty, zachované `smooth on/off` i blokované rizikové vnitřní direktivy, uzavření `wall`, zálohy a vyloučené složky. JavaScript byl zkontrolován pomocí `node --check`.

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
