import time
import threading
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError

uri = "bolt://localhost:7687"
user = "neo4j"
password = "zaritsky_fb41mp"

driver = GraphDatabase.driver(uri, auth=(user, password))

def initialize_likes_field(driver, item_id):
    with driver.session() as session:
        session.run("""
            MATCH (i:Item {id: $item_id})
            SET i.likes = 0
            """, item_id=item_id)

def increment_likes(driver, item_id, increments):
    with driver.session() as session:
        for _ in range(increments):
            session.run("""
                MATCH (i:Item {id: $item_id})
                SET i.likes = i.likes + 1
                """, item_id=item_id)

def get_likes(driver, item_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Item {id: $item_id})
            RETURN i.likes AS likes
            """, item_id=item_id)
        return result.single()["likes"]

def safe_increment_likes(driver, item_id, increments):
    retries = 5
    for _ in range(increments):
        success = False
        attempts = 0
        while not success and attempts < retries:
            try:
                increment_likes(driver, item_id, 1)
                success = True
            except TransientError:
                attempts += 1
                time.sleep(0.1) 

def run_threads(driver, item_id, num_threads, increments_per_thread):
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=safe_increment_likes, args=(driver, item_id, increments_per_thread))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    item_id = 1
    num_threads = 10 
    increments_per_thread = 10000

    print(f"Initializing 'likes' for the item with ID: {item_id}")
    initialize_likes_field(driver, item_id)

    start_time = time.time()

    print("Starting threads for incrementing...")
    run_threads(driver, item_id, num_threads, increments_per_thread)

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    total_likes = get_likes(driver, item_id)
    print(f"Final 'likes' count for item with ID {item_id}: {total_likes}")
    print(f"Execution time: {elapsed_time} seconds")




