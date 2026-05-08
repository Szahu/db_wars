import json
import time
import psycopg2
from psycopg2.extras import execute_values
from pymongo import MongoClient
from data_gen import ProductGenerator

# Konfiguracja baz danych
postgres_db_config = {
    "dbname": "janusz_market",
    "user": "postgres",
    "password": "",
    "host": "localhost",
    "port": "5432"
}

mongo_config = {
    "host": "localhost",
    "port": 27017,
    "db_name": "janusz_market",
    "collection_name": "produkty"
}

def reset_postgres(conn):
    try:
        cur = conn.cursor()
        print("\n--- [PG] Czyszczenie terenu pod inwestycję ---")
        cur.execute("DROP TABLE IF EXISTS produkty CASCADE;")
        cur.execute("""
            CREATE TABLE produkty (
                id SERIAL PRIMARY KEY,
                nazwa VARCHAR(255) NOT NULL,
                kategoria VARCHAR(100),
                cena DECIMAL(12, 2),
                atrybuty JSONB
            );
        """)
        cur.close()
        print("✅ [PG] Tabela 'produkty' gotowa.")
    except Exception as e:
        print(f"❌ [PG] Błąd Postgres: {e}")

def reset_mongodb():
    try:
        client = MongoClient(mongo_config["host"], mongo_config["port"])
        db = client[mongo_config["db_name"]]
        print("\n--- [MG] Schizma technologiczna w toku ---")
        db[mongo_config["collection_name"]].drop()
        db.create_collection(mongo_config["collection_name"])
        client.close()
        print("✅ [MG] Kolekcja 'produkty' gotowa.")
    except Exception as e:
        print(f"❌ [MG] Błąd MongoDB: {e}")

def load_data(total_records=1000000, batch_size=5000):
    gen = ProductGenerator()
    
    # Połączenia
    pg_conn = psycopg2.connect(**postgres_db_config)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    mg_client = MongoClient(mongo_config["host"], mongo_config["port"])
    mg_coll = mg_client[mongo_config["db_name"]][mongo_config["collection_name"]]

    print(f"\n🚀 Startujemy z gulaszem! Do załadowania: {total_records} rekordów (batch: {batch_size})")
    
    global_start = time.time()
    processed = 0

    try:
        while processed < total_records:
            # 1. Generowanie paczki
            current_batch = gen.generate_batch(batch_size)
            
            # 2. Przygotowanie danych dla Postgresa
            # Ważne: rzutujemy atrybuty na JSON string
            pg_batch = [
                (p['nazwa'], p['kategoria'], p['cena'], json.dumps(p['atrybuty']))
                for p in current_batch
            ]

            # 3. Wsad do Postgresa
            pg_start = time.time()
            execute_values(pg_cur, 
                "INSERT INTO produkty (nazwa, kategoria, cena, atrybuty) VALUES %s", 
                pg_batch
            )
            pg_end = time.time()

            # 4. Wsad do MongoDB (pamiętaj o skopiowaniu listy, bo Mongo dodaje _id do słowników)
            mg_start = time.time()
            mg_coll.insert_many(current_batch) 
            mg_end = time.time()

            processed += batch_size
            
            print(f"📦 [{processed}/{total_records}] | PG: {pg_end-pg_start:.3f}s | MG: {mg_end-mg_start:.3f}s")

    except Exception as e:
        print(f"❌ Błąd podczas ładowania: {e}")
    finally:
        pg_cur.close()
        pg_conn.close()
        mg_client.close()

    total_time = time.time() - global_start
    print(f"\n✅ Operacja zakończona! Całkowity czas: {total_time:.2f}s")

if __name__ == "__main__":
    # 1. Przygotowanie baz
    try:
        conn = psycopg2.connect(**postgres_db_config)
        conn.autocommit = True
        reset_postgres(conn)
        conn.close()
    except Exception as e:
        print(f"Błąd połączenia PG: {e}")

    reset_mongodb()

    # 2. Ładowanie danych
    # Na próbę możesz zmienić na 50000, żeby sprawdzić czy wszystko działa
    load_data(total_records=1000000, batch_size=5000)