import time
import psycopg2
from pymongo import MongoClient
import matplotlib.pyplot as plt
import gc # Garbage Collector do czyszczenia RAMu

# Import konfiguracji
from loader import postgres_db_config, mongo_config
from resource_monitor import ResourceMonitor

def plot_results(mg_monitor, pg_monitor):
    plt.figure(figsize=(12, 10))

    # --- Wykres CPU ---
    plt.subplot(2, 1, 1)
    plt.plot(mg_monitor.timestamps, mg_monitor.cpu_usage, label='MongoDB CPU %', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.cpu_usage, label='PostgreSQL CPU %', color='blue', linestyle='--')
    plt.title('Zużycie CPU podczas Eksperymentu 1 (Izolacja)')
    plt.xlabel('Czas (s)')
    plt.ylabel('CPU %')
    plt.legend()
    plt.grid(True)

    # --- Wykres RAM ---
    plt.subplot(2, 1, 2)
    plt.plot(mg_monitor.timestamps, mg_monitor.ram_usage, label='MongoDB RAM (MB)', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.ram_usage, label='PostgreSQL RAM (MB)', color='blue', linestyle='--')
    plt.title('Zużycie RAM (RSS) podczas Eksperymentu 1 (Izolacja)')
    plt.xlabel('Czas (s)')
    plt.ylabel('RAM (MB)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('eksperyment_1_wykres_izolacja.png')
    print("\n📊 Wykres zapisany jako 'eksperyment_1_wykres_izolacja.png'")
    plt.show()

def run_experiment_1_with_plots():
    print("🧪 EKSPERYMENT 1: Schema Evolution - PEŁNA IZOLACJA")

    # --- FAZA 1: MONGODB ---
    print("\n[1/2] Rozpoczynam test MongoDB...")
    monitor_mg = ResourceMonitor()
    
    # Otwieramy połączenie tylko na czas testu
    mg_client = MongoClient(mongo_config["host"], mongo_config["port"])
    mg_coll = mg_client[mongo_config["db_name"]][mongo_config["collection_name"]]
    
    monitor_mg.start()
    start_mg = time.time()
    
    # Wykonanie zadania
    mg_coll.update_many({}, {"$set": {"atrybuty.slad_weglowy": 12.5}})
    
    end_mg = time.time()
    monitor_mg.stop_flag = True
    monitor_mg.join()
    time.sleep(1) # Oddech dla monitora

    # Natychmiastowe sprzątanie i zamykanie połączenia Mongo
    print("🧹 Sprzątanie MongoDB i zamykanie połączenia...")
    mg_coll.update_many({}, {"$unset": {"atrybuty.slad_weglowy": ""}})
    mg_client.close()
    
    # Usuwanie obiektów i wymuszenie czyszczenia RAM przez Pythona
    del mg_client
    del mg_coll
    gc.collect() 
    
    print(f"✅ Faza MongoDB zakończona ({end_mg - start_mg:.2f}s). System oczyszczony.")
    time.sleep(2) # Przerwa techniczna między bazami

    # --- FAZA 2: POSTGRESQL ---
    print("\n[2/2] Rozpoczynam test PostgreSQL...")
    monitor_pg = ResourceMonitor()
    
    # Otwieramy połączenie tylko na czas testu
    pg_conn = psycopg2.connect(**postgres_db_config)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()
    
    monitor_pg.start()
    start_pg = time.time()
    
    # Wykonanie zadania
    pg_cur.execute("UPDATE produkty SET atrybuty = atrybuty || '{\"slad_weglowy\": 12.5}';")
    
    end_pg = time.time()
    monitor_pg.stop_flag = True
    monitor_pg.join()
    time.sleep(1)

    # Sprzątanie i zamykanie Postgresa
    print("🧹 Sprzątanie PostgreSQL i zamykanie połączenia...")
    pg_cur.execute("UPDATE produkty SET atrybuty = atrybuty - 'slad_weglowy';")
    pg_cur.close()
    pg_conn.close()
    
    del pg_conn
    del pg_cur
    gc.collect()

    print(f"✅ Faza PostgreSQL zakończona ({end_pg - start_pg:.2f}s).")

    # --- WIZUALIZACJA ---
    plot_results(monitor_mg, monitor_pg)

if __name__ == "__main__":
    run_experiment_1_with_plots()