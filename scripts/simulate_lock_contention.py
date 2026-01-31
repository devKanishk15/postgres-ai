"""
Lock Contention Simulation Script
Simulates lock waits and deadlocks for testing the chatbot's detection capabilities.
"""
import psycopg2
import threading
import time
import argparse
from datetime import datetime

def log(message: str):
    """Print timestamped log message."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def create_test_table(conn):
    """Create a test table for lock simulation."""
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS lock_test;
            CREATE TABLE lock_test (
                id SERIAL PRIMARY KEY,
                counter INTEGER DEFAULT 0,
                data TEXT
            );
            INSERT INTO lock_test (counter, data)
            SELECT generate_series, 'initial data'
            FROM generate_series(1, 100);
        """)
    conn.commit()
    log("Created lock_test table with 100 rows")


def session_a(dsn: str, row_id_1: int, row_id_2: int, hold_time: int):
    """
    Session A: Acquires lock on row_id_1, then tries to lock row_id_2.
    This can create a deadlock with session B.
    """
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    
    try:
        with conn.cursor() as cur:
            log(f"Session A: Locking row {row_id_1}...")
            cur.execute("UPDATE lock_test SET counter = counter + 1 WHERE id = %s", (row_id_1,))
            log(f"Session A: Got lock on row {row_id_1}")
            
            time.sleep(2)  # Give Session B time to lock row_id_2
            
            log(f"Session A: Trying to lock row {row_id_2}...")
            cur.execute("UPDATE lock_test SET counter = counter + 1 WHERE id = %s", (row_id_2,))
            log(f"Session A: Got lock on row {row_id_2}")
            
            time.sleep(hold_time)
            
        conn.commit()
        log("Session A: Committed")
    except Exception as e:
        log(f"Session A: Error - {e}")
        conn.rollback()
    finally:
        conn.close()


def session_b(dsn: str, row_id_1: int, row_id_2: int, hold_time: int):
    """
    Session B: Acquires lock on row_id_2, then tries to lock row_id_1.
    This creates a deadlock with session A.
    """
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    
    time.sleep(1)  # Let Session A start first
    
    try:
        with conn.cursor() as cur:
            log(f"Session B: Locking row {row_id_2}...")
            cur.execute("UPDATE lock_test SET counter = counter + 1 WHERE id = %s", (row_id_2,))
            log(f"Session B: Got lock on row {row_id_2}")
            
            time.sleep(2)  # Give deadlock time to form
            
            log(f"Session B: Trying to lock row {row_id_1}...")
            cur.execute("UPDATE lock_test SET counter = counter + 1 WHERE id = %s", (row_id_1,))
            log(f"Session B: Got lock on row {row_id_1}")
            
            time.sleep(hold_time)
            
        conn.commit()
        log("Session B: Committed")
    except Exception as e:
        log(f"Session B: Error - {e}")
        conn.rollback()
    finally:
        conn.close()


def long_running_lock(dsn: str, row_ids: list, hold_time: int):
    """Hold locks on multiple rows for an extended period."""
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    
    try:
        with conn.cursor() as cur:
            for row_id in row_ids:
                log(f"Long Lock: Locking row {row_id}...")
                cur.execute("SELECT * FROM lock_test WHERE id = %s FOR UPDATE", (row_id,))
            
            log(f"Long Lock: Holding {len(row_ids)} row locks for {hold_time} seconds...")
            time.sleep(hold_time)
            
        conn.commit()
        log("Long Lock: Released all locks")
    except Exception as e:
        log(f"Long Lock: Error - {e}")
        conn.rollback()
    finally:
        conn.close()


def waiting_sessions(dsn: str, row_ids: list, num_waiters: int):
    """Create multiple sessions waiting for the same locks."""
    time.sleep(2)  # Let long_running_lock acquire locks first
    
    def waiter(session_id: int):
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        
        try:
            with conn.cursor() as cur:
                for row_id in row_ids:
                    log(f"Waiter {session_id}: Waiting for row {row_id}...")
                    cur.execute("UPDATE lock_test SET counter = counter + 1 WHERE id = %s", (row_id,))
                    log(f"Waiter {session_id}: Got lock on row {row_id}")
            
            conn.commit()
            log(f"Waiter {session_id}: Completed")
        except Exception as e:
            log(f"Waiter {session_id}: Error - {e}")
            conn.rollback()
        finally:
            conn.close()
    
    threads = []
    for i in range(num_waiters):
        t = threading.Thread(target=waiter, args=(i + 1,))
        t.start()
        threads.append(t)
        time.sleep(0.5)  # Stagger the waiters
    
    for t in threads:
        t.join()


def main():
    parser = argparse.ArgumentParser(description="Simulate lock contention scenarios")
    parser.add_argument("--host", default="postgres", help="PostgreSQL host")
    parser.add_argument("--port", default=5432, type=int, help="PostgreSQL port")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--password", default="postgres", help="PostgreSQL password")
    parser.add_argument("--database", default="testdb", help="PostgreSQL database")
    parser.add_argument("--mode", default="deadlock", 
                        choices=["deadlock", "long_lock", "contention"],
                        help="Simulation mode")
    parser.add_argument("--hold-time", default=60, type=int, 
                        help="How long to hold locks (seconds)")
    parser.add_argument("--waiters", default=5, type=int,
                        help="Number of waiting sessions (for contention mode)")
    
    args = parser.parse_args()
    
    dsn = f"postgresql://{args.user}:{args.password}@{args.host}:{args.port}/{args.database}"
    
    log("=" * 60)
    log("Lock Contention Simulation")
    log("=" * 60)
    log(f"Mode: {args.mode}")
    log(f"Hold Time: {args.hold_time}s")
    log("=" * 60)
    
    # Create test table
    conn = psycopg2.connect(dsn)
    create_test_table(conn)
    conn.close()
    
    if args.mode == "deadlock":
        log("\nStarting DEADLOCK simulation...")
        log("Session A will lock row 1, then try row 2")
        log("Session B will lock row 2, then try row 1")
        log("")
        
        thread_a = threading.Thread(target=session_a, args=(dsn, 1, 2, args.hold_time))
        thread_b = threading.Thread(target=session_b, args=(dsn, 1, 2, args.hold_time))
        
        thread_a.start()
        thread_b.start()
        
        thread_a.join()
        thread_b.join()
        
    elif args.mode == "long_lock":
        log("\nStarting LONG LOCK simulation...")
        log(f"Holding locks on rows 1-10 for {args.hold_time} seconds")
        log("")
        
        long_running_lock(dsn, list(range(1, 11)), args.hold_time)
        
    elif args.mode == "contention":
        log("\nStarting CONTENTION simulation...")
        log(f"One long lock + {args.waiters} waiting sessions")
        log("")
        
        lock_thread = threading.Thread(
            target=long_running_lock, 
            args=(dsn, list(range(1, 6)), args.hold_time)
        )
        wait_thread = threading.Thread(
            target=waiting_sessions,
            args=(dsn, list(range(1, 6)), args.waiters)
        )
        
        lock_thread.start()
        wait_thread.start()
        
        lock_thread.join()
        wait_thread.join()
    
    log("")
    log("Simulation complete.")


if __name__ == "__main__":
    main()
