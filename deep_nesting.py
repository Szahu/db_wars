import time
import psycopg2
import gc
import matplotlib.pyplot as plt
from pymongo import MongoClient
from loader import postgres_db_config, mongo_config
from resource_monitor import ResourceMonitor

def plot_deep_nesting_results(mg_monitor, pg_monitor):
    plt.figure(figsize=(12, 10))

    # --- Wykres CPU ---
    plt.subplot(2, 1, 1)
    plt.plot(mg_monitor.timestamps, mg_monitor.cpu_usage, label='MongoDB CPU %', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.cpu_usage, label='PostgreSQL CPU %', color='blue', linestyle='--')
    plt.title('Zużycie CPU: Deep Nesting Search (Index [1])')
    plt.xlabel('Czas (s)')
    plt.ylabel('CPU %')
    plt.legend()
    plt.grid(True)

    # --- Wykres RAM ---
    plt.subplot(2, 1, 2)
    plt.plot(mg_monitor.timestamps, mg_monitor.ram_usage, label='MongoDB RAM (MB)', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.ram_usage, label='PostgreSQL RAM (MB)', color='blue', linestyle='--')
    plt.title('Zużycie RAM: Deep Nesting Search (Index [1])')
    plt.xlabel('Czas (s)')
    plt.ylabel('RAM (MB)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('eksperyment_2_wykres.png')
    print("\n📊 Wykres zapisany jako 'eksperyment_2_wykres.png'")
    plt.show()

def run_experiment_2_with_plots():
    print("🧪 EKSPERYMENT 2: Deep Nesting - Monitorowanie wydajności...")

    # --- FAZA 1: MONGODB ---
    print("\n[1/2] Testowanie MongoDB...")
    monitor_mg = ResourceMonitor(interval=0.01)
    mg_client = MongoClient(mongo_config["host"], mongo_config["port"])
    db = mg_client[mongo_config["db_name"]]
    coll = db[mongo_config["collection_name"]]

    monitor_mg.start()
    start_mg = time.time()

    # Wykonujemy rzeczywiste zapytanie (nie tylko explain), aby obciążyć system
    mongo_filter = {
        "$or": [
            {"atrybuty.certyfikaty.1.data": {"$regex": "^2025"}},
            {"atrybuty.certyfikaty.1.data": {"$regex": "^2026"}}
        ]
    }
    # Używamy list(), aby wymusić pobranie wszystkich wyników z kursora
    results_mg = list(coll.find(mongo_filter))
    
    end_mg = time.time()
    monitor_mg.stop_flag = True
    monitor_mg.join()
    time.sleep(1) # Oddech

    print(f"✅ Mongo znalazło {len(results_mg)} rekordów w {end_mg - start_mg:.2f}s")

    # POBIERANIE EXPLAIN DLA MONGO
    explain_mg = db.command('explain', {'find': mongo_config["collection_name"], 'filter': mongo_filter}, verbosity='executionStats')
    
    print("\n--- 📝 MONGO EXPLAIN SUMMARY ---")
    e_stats = explain_mg.get('executionStats', {})
    print(e_stats)

    mg_client.close()
    del mg_client, results_mg
    gc.collect()
    time.sleep(2)

    # --- FAZA 2: POSTGRESQL ---
    print("\n[2/2] Testowanie PostgreSQL...")
    monitor_pg = ResourceMonitor(interval=0.01)
    pg_conn = psycopg2.connect(**postgres_db_config)
    pg_cur = pg_conn.cursor()

    monitor_pg.start()
    start_pg = time.time()

    pg_query = """
    SELECT * FROM produkty 
    WHERE (atrybuty->'certyfikaty'->1->>'data' LIKE '2025%')
       OR (atrybuty->'certyfikaty'->1->>'data' LIKE '2026%');
    """
    pg_cur.execute(pg_query)
    results_pg = pg_cur.fetchall()

    end_pg = time.time()
    monitor_pg.stop_flag = True
    monitor_pg.join()
    time.sleep(1)

    print(f"✅ Postgres znalazł {len(results_pg)} rekordów w {end_pg - start_pg:.2f}s")

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
    plot_deep_nesting_results(monitor_mg, monitor_pg)

if __name__ == "__main__":
    run_experiment_2_with_plots()