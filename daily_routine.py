import time
import psycopg2
import gc
import matplotlib.pyplot as plt
from pymongo import MongoClient
from loader import postgres_db_config, mongo_config
from resource_monitor import ResourceMonitor

def plot_routine_results(mg_monitor, pg_monitor):
    plt.figure(figsize=(12, 10))

    plt.subplot(2, 1, 1)
    plt.plot(mg_monitor.timestamps, mg_monitor.cpu_usage, label='MongoDB CPU %', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.cpu_usage, label='PostgreSQL CPU %', color='blue', linestyle='--')
    plt.title('Zużycie CPU: Codzienna Rutyna (Średnia + Update + Rollback)')
    plt.xlabel('Czas (s)')
    plt.ylabel('CPU %')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(mg_monitor.timestamps, mg_monitor.ram_usage, label='MongoDB RAM (MB)', color='green')
    plt.plot(pg_monitor.timestamps, pg_monitor.ram_usage, label='PostgreSQL RAM (MB)', color='blue', linestyle='--')
    plt.title('Zużycie RAM: Codzienna Rutyna')
    plt.xlabel('Czas (s)')
    plt.ylabel('RAM (MB)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('eksperyment_rutyna_wykres.png')
    print("\n📊 Wykres zapisany jako 'eksperyment_rutyna_wykres.png'")
    plt.show()

def run_daily_routine():
    print("🧪 EKSPERYMENT BONUSOWY: Codzienna Rutyna (Globalna Średnia i Masowy Update)")

    # --- FAZA 1: MONGODB ---
    print("\n[1/2] Testowanie MongoDB...")
    monitor_mg = ResourceMonitor(interval=0.1)
    mg_client = MongoClient(mongo_config["host"], mongo_config["port"])
    coll = mg_client[mongo_config["db_name"]][mongo_config["collection_name"]]

    monitor_mg.start()
    
    # Krok 1: Globalna średnia cena
    t0 = time.time()
    avg_price_mg = list(coll.aggregate([{"$group": {"_id": None, "srednia": {"$avg": "$cena"}}}]))
    t1 = time.time()
    print(f"✅ Mongo [Odczyt]: Średnia cena {avg_price_mg[0]['srednia']:.2f} policzona w {t1-t0:.2f}s")

    # Krok 2: Zdublowanie/Modyfikacja nazwy (Wymaga Mongo 4.2+ dla potoku w update)
    t2 = time.time()
    coll.update_many({}, [{"$set": {"nazwa": {"$concat": ["$nazwa", " (PROMO)"]}}}])
    t3 = time.time()
    print(f"✅ Mongo [Update]: Dodano '(PROMO)' do miliona nazw w {t3-t2:.2f}s")

    # Krok 3: Sprzątanie - usunięcie dopisku (Wymaga Mongo 4.4+ dla $replaceAll)
    t4 = time.time()
    coll.update_many({}, [{"$set": {"nazwa": {"$replaceAll": {"input": "$nazwa", "find": " (PROMO)", "replacement": ""}}}}])
    t5 = time.time()
    print(f"✅ Mongo [Cleanup]: Usunięto dopiski w {t5-t4:.2f}s")

    monitor_mg.stop_flag = True
    monitor_mg.join()
    mg_client.close()
    del mg_client
    gc.collect()
    time.sleep(2)

    # --- FAZA 2: POSTGRESQL ---
    print("\n[2/2] Testowanie PostgreSQL...")
    monitor_pg = ResourceMonitor(interval=0.1)
    pg_conn = psycopg2.connect(**postgres_db_config)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    monitor_pg.start()

    # Krok 1: Globalna średnia cena
    t0 = time.time()
    pg_cur.execute("SELECT AVG(cena) FROM produkty;")
    avg_price_pg = pg_cur.fetchone()[0]
    t1 = time.time()
    print(f"✅ Postgres [Odczyt]: Średnia cena {avg_price_pg:.2f} policzona w {t1-t0:.2f}s")

    # Krok 2: Zdublowanie/Modyfikacja nazwy
    t2 = time.time()
    pg_cur.execute("UPDATE produkty SET nazwa = nazwa || ' (PROMO)';")
    t3 = time.time()
    print(f"✅ Postgres [Update]: Dodano '(PROMO)' do miliona nazw w {t3-t2:.2f}s")

    # Krok 3: Sprzątanie - usunięcie dopisku
    t4 = time.time()
    pg_cur.execute("UPDATE produkty SET nazwa = REPLACE(nazwa, ' (PROMO)', '');")
    t5 = time.time()
    print(f"✅ Postgres [Cleanup]: Usunięto dopiski w {t5-t4:.2f}s")

    monitor_pg.stop_flag = True
    monitor_pg.join()
    pg_cur.close()
    pg_conn.close()
    del pg_conn
    gc.collect()

    # --- WIZUALIZACJA ---
    plot_routine_results(monitor_mg, monitor_pg)

if __name__ == "__main__":
    run_daily_routine()