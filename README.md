# Therion TH2 Inspector – verze 7 (experimentální)

Lokální Python/HTML kontrola a schvalování vybraných oprav souborů `.th2`. Není oficiální součástí Therionu.

## Spuštění na Windows

1. Rozbal ZIP do jedné složky.
2. Spusť `SPUSTIT_KONTROLU.bat`, zadej cestu k adresáři mapy.
3. V prohlížeči se otevře lokální server `127.0.0.1`.
4. Zkontroluj nálezy a náhled. **Zelená přerušovaná křivka** ukazuje návrh změny Bézierových táhel.
5. U každé změny klikni na „Schválit“. Před zápisem zvol „Zobrazit plán změn“ a „Zálohovat a provést schválené změny“.

Alternativně `py therion_kontrola.py "C:\\mapy\\jeskyne" --near 1.0`.

## Co umí

- Duplicitní body: přímý nulový úsek lze odstranit také bezprostředně po Bézierově segmentu. Malou uzavřenou Bézierovu smyčku lze odstranit jako celý segment při maximální vzdálenosti obou táhel do 30 jednotek od shodného koncového bodu. Nesousedící duplicity zůstávají pouze ke kontrole.
- Samoprotínající se jeden Bézierův segment: nabídne alternativní křivku postupným přibližováním řídicích bodů k přímému spojení koncových bodů. Původní čára červeně, návrh zeleně přerušovaně. **Jde o geometrický návrh, nikoliv doklad vhodnosti pro mapu.** Schválením se mění pouze řídicí body (první čtyři hodnoty šestice); koncový bod zůstává beze změny.
- Chybějící `-close on`: pouze u `chimney`, `pit`, `border`, `rock-border` se přesně shodnými počátečními a koncovými souřadnicemi.
- Sloučení čar: pro přímou přesnou návaznost **konec A → začátek B**, stejné celé hlavičky `line`, stejný scrap, bez větvení, ID, `-reverse` a bez vnitřních direktiv/komentářů. Obě čáry mohou být vzdálené v souboru nebo zapsané v opačném pořadí. Nástroj přesune do výsledné čáry geometrii druhé čáry beze změny Bézierových táhel, její definici odstraní; ostatní čáry mezi nimi zůstanou. Pokud nějaká podmínka neplatí, ukáže pouze upozornění.
- Téměř navazující čáry (nenulová mezera): pouze kontrola, bez automatických oprav.

**Před automatickým sloučením zkontroluj směr a typ:** návrhy vyžadující otočení čáry, `-reverse`, jiné atributy, samostatná ID nebo vnitřní direktivy nejsou automaticky schvalovatelné.

## Zálohování a omezení

Před úpravou originálů se vytvoří `_Therion_zalohy/<čas>/` s kopií **pouze měněných souborů** a `protokol.json`. Soubory, které se změnily od posledního prohledání, se neupraví. Záloha a adresáře `data` se při skenování ignorují (bez ohledu na velikost písmen).

Nástroj neodhalí všechny možné příčiny hlášení „scrap outline intersects itself“. Návrhy oprav samoprotínajících se segmentů mohou **viditelně změnit tvar stěny** a jsou určeny k pečlivému vizuálnímu schválení. Při první práci použij kopii celého projektu a výsledek ověř v Therionu.

Hromadná dávka odmítne konfliktní sloučení (stejná čára ve více návrzích), překryv sloučení s další opravou dané čáry i vícenásobnou úpravu téhož segmentu. Verze 7 umí schválit celý jednoznačný řetězec tří a více čar jedním krokem. Překryvy návrhů se zobrazují už při výběru a server je rovněž odmítne.

## Testy

`py -m unittest discover -s tests -v`

Testována přesná a téměř přesná návaznost, spojení vzdálených definic, odmítnutí `-reverse` a vnitřních direktiv, duplicita po Bézierově segmentu, uzavření, záloha a smyčka na řádku 1399 dodaného souboru Škaredá chodba (fixture je volitelná).

## GitHub

https://github.com/matls/therion-th2-inspector

## Novinky verze 7

- Nový filtr **Možnost opravy**: Všechny možnosti / Lze opravit / Pouze kontrola, společně s ostatními filtry. Počty nalezených oprav a případů pro ruční kontrolu se zobrazují v levém panelu.
- Schválení sloučení jedné dvojice zabrání současnému schválení další operace zahrnující stejnou čáru. V nálezu se zobrazuje důvod konfliktu. Totéž platí pro souběh sloučení a jiné opravy stejné čáry. Backend ověřuje konflikty znovu, nezávisle na rozhraní.
- **Celé řetězce**: samostatná kategorie pro jednoznačné směrované řetězce tří a více čar. Spojí je jediná atomická operace. Čáry mohou být v souboru na různých místech a v jiném pořadí. Náhled ukazuje jednotlivé části různými barvami.
- Automaticky se slučují jen přesně navazující čáry (konec → začátek), se stejnými parametry, bez `-id`, `-reverse`, interních direktiv a komentářů, a bez rozvětvení. Uzavřené nebo cyklické řetězce, nejednoznačné návaznosti a obrácené geometrické směry zůstávají mimo automatické sloučení.
- Před schválením zkontroluj geometrii a výsledný směr. Ani přísná syntaktická kontrola nemůže posoudit kartografický záměr. Nejdřív vyzkoušej na kopii projektu a výstup ověř v Therionu.

### Kontrola vývojové verze

```bat
py -m unittest discover -s tests -v
```

JavaScript v HTML musí projít syntaktickou kontrolou při sestavování balíčku (Node.js `node --check`).