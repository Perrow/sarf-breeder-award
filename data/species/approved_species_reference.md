# Godkända arter och odlingsvalörer

Källan är den föreningslista som låg till grund för DATA-002. Endast rader med valör **Brons**, **Silver** eller **Guld** har tagits med; rader utan valör och rader markerade som odlingsvariant utan extrapoäng är exkluderade.

Efter normalisering och deduplicering innehåller referensen 108 taxa:

- 46 brons
- 40 silver
- 22 guld

`approved_species_reference.csv` är den fullständiga referenslistan. Kolumnen `needs_swedish_name=yes` markerar taxa där källan saknar svenskt populärnamn och där inget tillräckligt säkert svenskt namn har hittats. Dessa har inte fått något påhittat namn.

`approved_species_import.json` innehåller de 47 nya taxa som har ett svenskt namn och därför kan importeras med nuvarande importmotor. Tio taxa finns redan i de tidigare importfilerna och dupliceras inte där. För `Trichopodus trichopterus` har den tidigare importfilens valör ändrats från silver till brons eftersom källdokumentet är facit.

Några vetenskapliga namn har normaliserats när ändringen kunnat verifieras säkert, bland annat:

- `Corydoras duplicareus` → `Hoplisoma duplicareum`
- `Corydoras nanus` → `Gastrodermus nanus`
- `Corydoras paleatus` → `Hoplisoma paleatum`
- `Cichlasoma salvini` → `Trichromis salvini`
- `Lamprologus multifasciatus` → `Neolamprologus multifasciatus`
- `Xiphophorus helleri` → `Xiphophorus hellerii`
- `Neocaridina davidii` → `Neocaridina davidi`
- `Hypancistrus sp. L333` → `Hypancistrus seideli`

C-, CW- och L-nummer har bevarats. För obeskrivna `sp.`-taxa med sådana nummer ingår numret även i `scientific_name` i importfilen så att exempelvis olika `Ancistrus sp.` inte kolliderar med varandra.

## Källor för kompletterade namn och taxonomi

- FishBase: vetenskapliga namn och engelska namn
- Zoopet: svenska handels-/populärnamn
- Corydoras World: aktuell placering av Corydoradinae och C/CW-nummer
- Herkules Zoo: svenskt namn för CW010

Källfilens odlingsvalör har alltid prioritet framför andra webbplatser.
