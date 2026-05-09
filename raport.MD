# Raport Wojny baz danych Janusz Market

Autorzy:
 - Stanisław Solarewicz ss443488
 - Gem Ini3 gm123456

## Porównanie rozmiaru baz danych
Dla identycznego zestawu miliona rekordów wyniki są następujące:

`SELECT pg_size_pretty(pg_relation_size('produkty'));` daje 314MB
\
`SELECT pg_size_pretty(pg_total_relation_size('produkty'));` daje 336MB

natomiast `db.produkty.stats()` zwraca `size: 314976346` oraz `storageSize: 135581696`.

Czyli mamy 336MB dla postgresa oraz 136MB dla Mongo. Poniekąd szokujący wynik, jednak wyjaśnienie jest proste, Mongo jest dwa razy mniejsze dzięki agresywnej kompresji atrybutów, czego Postgres nie robi tak dobrze z JSONB.