import time
import psycopg2
import gc
import matplotlib.pyplot as plt
from pymongo import MongoClient
from loader import postgres_db_config, mongo_config
from resource_monitor import ResourceMonitor

def plot_aggregation_results(mg_monitor, pg_monitor):
    plt.figure(figsize=(12, 10))

    # --- Wykres CPU ---
    plt.subplot(2, 1, 1)
    plt.plot(mg_monitor.timestamps, mg_monitor.cpu_usage, label='MongoDB CPU %', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.cpu_usage, label='PostgreSQL CPU %', color='blue', linestyle='--')
    plt.title('Zużycie CPU: Eksperyment 3 (Agregacja i GROUP BY)')
    plt.xlabel('Czas (s)')
    plt.ylabel('CPU %')
    plt.legend()
    plt.grid(True)

    # --- Wykres RAM ---
    plt.subplot(2, 1, 2)
    plt.plot(mg_monitor.timestamps, mg_monitor.ram_usage, label='MongoDB RAM (MB)', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.ram_usage, label='PostgreSQL RAM (MB)', color='blue', linestyle='--')
    plt.title('Zużycie RAM: Eksperyment 3 (Agregacja i GROUP BY)')
    plt.xlabel('Czas (s)')
    plt.ylabel('RAM (MB)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('eksperyment_3_wykres.png')
    print("\n📊 Wykres zapisany jako 'eksperyment_3_wykres.png'")
    plt.show()

def run_experiment_3_aggregation():
    print("🧪 EKSPERYMENT 3: Agregacja na Kwasie - Średnia cena po typie zasilania")

    # --- FAZA 1: MONGODB ---
    print("\n[1/2] Testowanie MongoDB (Aggregation Pipeline)...")
    monitor_mg = ResourceMonitor(interval=0.05) # Szybsze próbkowanie dla dokładności
    mg_client = MongoClient(mongo_config["host"], mongo_config["port"])
    db = mg_client[mongo_config["db_name"]]
    coll = db[mongo_config["collection_name"]]

    pipeline = [
        {
            "$group": {
                "_id": "$atrybuty.zasilanie",
                "srednia_cena": { "$avg": "$cena" },
                "liczba_produktow": { "$sum": 1 }
            }
        },
        {
            "$sort": { "_id": 1 } # 1 to sortowanie rosnące (A-Z)
        }
    ]

    monitor_mg.start()
    start_mg = time.time()
    
    # Wykonanie agregacji
    results_mg = list(coll.aggregate(pipeline))
    
    end_mg = time.time()
    monitor_mg.stop_flag = True  # Zatrzymanie natychmiastowe
    monitor_mg.join()

    print(f"✅ Mongo przetworzyło agregację w {end_mg - start_mg:.2f}s")
    print("Przykładowe wyniki (Mongo):", results_mg[:2])

    # POBIERANIE EXPLAIN DLA MONGO (Agregacja)
    print("\n--- 📝 MONGO EXPLAIN (Agregacja) ---")
    explain_mg = db.command('explain', {'aggregate': mongo_config["collection_name"], 'pipeline': pipeline, 'cursor': {}}, verbosity='executionStats')

    # Dla agregacji struktura explain jest inna, wyciągamy główne fazy
    stages = explain_mg.get('stages', [])
    if stages:
        first_stage = stages[0].get('$cursor', {}).get('queryPlanner', {}).get('winningPlan', {}).get('stage', 'N/A')
        print(f"Plan (Stage 1): {first_stage}")
    else:
        print("Plan: Zoptymalizowany Pipeline")
    
    mg_client.close()
    del mg_client, results_mg
    gc.collect()
    time.sleep(2)

    # --- FAZA 2: POSTGRESQL ---
    print("\n[2/2] Testowanie PostgreSQL (GROUP BY JSONB)...")
    monitor_pg = ResourceMonitor(interval=0.05)
    pg_conn = psycopg2.connect(**postgres_db_config)
    pg_cur = pg_conn.cursor()

    pg_query = """
    SELECT 
        atrybuty->>'zasilanie' AS zasilanie,
        AVG(cena) AS srednia_cena,
        COUNT(*) AS liczba_produktow
    FROM produkty
    GROUP BY atrybuty->>'zasilanie'
    ORDER BY zasilanie;
    """

    monitor_pg.start()
    start_pg = time.time()
    
    # Wykonanie zapytania
    pg_cur.execute(pg_query)
    results_pg = pg_cur.fetchall()
    
    end_pg = time.time()
    monitor_pg.stop_flag = True  # Zatrzymanie natychmiastowe
    monitor_pg.join()

    print(f"✅ Postgres przetworzył agregację w {end_pg - start_pg:.2f}s")
    print("Przykładowe wyniki (Postgres):", results_pg[:2])

    # POBIERANIE EXPLAIN ANALYZE DLA PG
    print("\n--- 📝 POSTGRES EXPLAIN ANALYZE ---")
    pg_cur.execute("EXPLAIN ANALYZE " + pg_query)
    explain_lines = pg_cur.fetchall()
    for line in explain_lines:
        print(line[0])

    pg_cur.close()
    pg_conn.close()
    del pg_conn, results_pg
    gc.collect()

    # --- WIZUALIZACJA ---
    plot_aggregation_results(monitor_mg, monitor_pg)

if __name__ == "__main__":
    run_experiment_3_aggregation()