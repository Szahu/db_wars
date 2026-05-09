# ⚔️ Dziennik Bojowy z Wojny Baz Danych: Omni-Janusz-Market

**Zespół Audytorski:**
* Stanisław Solarewicz (ss443488) – Główny Inżynier Polowy
* Gem Ini3 (gm123456) – Młodszy Asystent ds. AI

**Kontekst Operacyjny (Setup Środowiska):**
Na potrzeby audytu zbudowaliśmy potężny generator polimorficznego "gulaszu atrybutów". Wygenerował on okrągły **milion (1 000 000) rekordów**, zanieczyszczając bazę produktami takimi jak używane procesory, "Turbo-Wiertarki Zemsta Sąsiada" czy wegański jarmuż. Zadbano o pełne zróżnicowanie: różne typy danych (float, boolean, zagnieżdżone tablice, obiekty). Bazy otrzymały dokładnie ten sam strumień danych (dzięki stałemu ziarnu losowości `seed=42`), co gwarantuje uczciwość pojedynku.

---

## 📊 Eksperyment 0: "Puchnięcie Danych" (Storage Efficiency)

*Pan Janusz płaci za dyski w serwerowni z własnej kieszeni, więc rozmiar ma znaczenie.*

**Hipoteza:** Myślałem, że MongoDB zmarnuje mnóstwo miejsca, ponieważ w każdym z miliona dokumentów musi powtarzać nazwy kluczy (np. `"zasilanie"`, `"certyfikaty"`). Z kolei Postgres, jako relacyjna opoka, wyjdzie z tego obronną ręką, bo przechowuje sztywny schemat tabeli.

**Procedura:** Zbadano realny rozmiar zajmowany przez identyczny zestaw miliona rekordów. W Postgresie użyto `pg_total_relation_size`, a w MongoDB `db.collection.stats()`.

**Werdykt:** Bezwzględne zwycięstwo **MongoDB**.
* **PostgreSQL:** `336 MB` (całkowity rozmiar z indeksami; same dane `314 MB`).
* **MongoDB:** `135 MB` (`storageSize`), mimo że nieskompresowane dane (`size`) ważyły `314 MB`.

**Uzasadnienie:** Szokujący wynik tłumaczy potężny silnik kompresji WiredTiger w MongoDB. Mimo powtarzania kluczy, Mongo agresywnie ściska dane na dysku. Postgres traktuje JSONB priorytetowo pod kątem szybkości dostępu (format binarny), nie stosując domyślnej kompresji dla mniejszych rekordów.

---

## 🧪 Eksperyment 1: "Zemsta Dynamicznego Marketingu" (Schema Evolution)

*Szef marketingu wymyślił, że od dziś każdy produkt musi być EKO.*

**Hipoteza:** Dodanie nowej cechy (`ślad_węglowy`) do miliona rekordów "w locie" zabije Postgresa (konieczność fizycznej aktualizacji JSONB), a Mongo nawet nie zauważy, że zmienił mu się schemat.

**Procedura:** Zmierzono czas, użycie CPU i RAM podczas dodawania nowego pola do każdego rekordu. W Mongo użyto operatora `$set`, a w Postgresie operatora scalania `||`.

**Werdykt:** Zdecydowane zwycięstwo **MongoDB**.
Wykresy użycia zasobów bezlitośnie obnażyły słabość "Betonu SQL". Postgres spowodował gigantyczny wystrzał zużycia procesora, podczas gdy linia MongoDB pozostała niemal płaska.

**Uzasadnienie:** Mongo po prostu dopisało nowe pole do dokumentów w locie. Postgres, jako baza transakcyjna (ACID), korzysta z mechanizmu MVCC (Multi-Version Concurrency Control). Aby zaktualizować JSONB, musiał de facto skopiować milion całych wierszy do nowych lokalizacji na dysku, obciążając I/O i procesor.

![Wykres - Eksperyment 1](./eksperyment_1_wykres_izolacja.png)

---

## 🧪 Eksperyment 2: "Głębokie Nurkowanie w Śmietniku" (Deep Nesting)

*Szukamy wszystkich narzędzi, w których DRUGI certyfikat na liście został wydany w 2025 lub 2026 roku.*

**Hipoteza:** Szukanie produktu po konkretnym indeksie tablicy (`certyfikaty[1]`) będzie drogą przez mękę w Postgresie, podczas gdy Mongo płynnie odnajdzie się w natywnym BSON-ie.

**Procedura:** Brak indeksów ułatwiających zadanie. Wykonano zapytania zagnieżdżone:
* **PG:** `WHERE (atrybuty->'certyfikaty'->1->>'data' LIKE '2025%') OR ...`
* **MG:** `"$or": [{"atrybuty.certyfikaty.1.data": {"$regex": "^2025"}}, ...]`

**Werdykt:** Szokujące zwycięstwo **PostgreSQL**.
* **Postgres:** 9970 wyników w **142 ms**.
* **Mongo:** 9970 wyników w **366 ms**.

**Uzasadnienie:** `EXPLAIN ANALYZE` ujawniło genialny ruch Postgresa. Baza zorientowała się, że brakuje indeksu, więc odpaliła `Parallel Seq Scan` (Workers Launched: 2). Rzuciła w problem dodatkowymi rdzeniami procesora, co widać jako potężny skok CPU na wykresie. Mongo działało jednowątkowo – posłusznie wykonało `COLLSCAN` (totalDocsExamined: 1 000 000), przegrywając wyścig z czasem.

![Wykres - Eksperyment 2](./eksperyment_2_wykres.png)

---

## 🧪 Eksperyment 3: "Agregacja na Kwasie" (The Analytic Crunch)

*Pan Janusz chce wiedzieć, po ile średnio chodzą maszyny na różnym typie zasilania.*

**Hipoteza:** MongoDB ze swoim zoptymalizowanym, kaskadowym *Aggregation Pipeline* zniszczy Postgresa w operacjach grupowania polimorficznych danych.

**Procedura:** Pogrupowano produkty według wartości wyciąganej ze środka gulaszu (`atrybuty.zasilanie`) i wyliczono średnią cenę.

**Werdykt:** Miażdżące zwycięstwo **PostgreSQL**.
* **Postgres:** **~295 ms** (0.21s bez narzutu planowania EXPLAIN).
* **Mongo:** **560 ms**.

**Uzasadnienie:** Kiedy dochodzi do brutalnej matematyki i rzucania tabelami w pamięci operacyjnej, relacyjne korzenie Postgresa to potęga. Użył on algorytmów `GroupAggregate` i zewnętrznego sortowania zlewnego (external merge Sort), przerabiając milion rekordów w ułamku sekundy. O dziwo, konieczność wyciągania wartości z JSONB (operator `->>`) wcale go nie spowolniła w stosunku do natywnego grupowania BSON w Mongo.

![Wykres - Eksperyment 3](./eksperyment_3_wykres.png)

---

## 🎁 Eksperyment Bonusowy: "Codzienna Rutyna na Black Friday"

*Testujemy surową wydajność operacji biznesowych (Odczyt -> Modyfikacja nazwy -> Cofnięcie).*

**Hipoteza:** Zwykłe zapytania CRUD pokażą zrównoważoną wydajność, ale aktualizacja pojedynczego, prostego pola (`nazwa`) ujawni przewagę Mongo w in-place updates.

**Procedura:** Obliczono średnią z całej bazy, następnie doklejono do miliona nazw string `(PROMO)`, po czym go usunięto.

**Werdykt:** Remis z naciskiem na **PostgreSQL** za surową prędkość.

| Operacja | PostgreSQL | MongoDB |
| :--- | :--- | :--- |
| **Odczyt (Średnia globalna)** | **0.10s** | 0.35s |
| **Update (Dodanie PROMO)** | **3.43s** | 4.11s |
| **Cleanup (Usunięcie PROMO)**| 5.64s | **4.25s** |

**Uzasadnienie:** Postgres po raz kolejny udowodnił, że relacyjny silnik wykonuje proste zadania matematyczne (globalne `AVG`) natychmiastowo. Przy zmianach tekstowych walka była wyrównana, jednak długi czas sprzątania (Cleanup) w Postgresie to znów pokłosie architektury MVCC, która przy częstych aktualizacjach musi nieustannie "odkurzać" stare wersje wierszy.

![Wykres - Rutyna](./eksperyment_rutyna_wykres.png)

---

### 🏆 Podsumowanie Audytu dla Omni-Janusz-Market
**Frakcja "Beton SQL"** może świętować. PostgreSQL poradził sobie z potwornym "Gulaszem Atrybutów" o wiele lepiej, niż zakładała hipoteza, deklasując Mongo w czasach agregacji i wielowątkowym przeszukiwaniu – co udowadnia, że typ JSONB to potężne i w pełni produkcyjne narzędzie. **Frakcja "Web-Scale Mongo"** zdobywa jednak punkty za fenomenalną kompresję dyskową (135 MB!) i niesamowitą stabilność zużycia zasobów (CPU/RAM) przy masowych aktualizacjach schematu. 

Panie Januszu – do analizy zysków wybieramy Postgresa, ale rachunki za dyski w serwerowni zdecydowanie zoptymalizuje Mongo!