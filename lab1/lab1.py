import hazelcast
import threading
import time

counter_t1 = 0 

def task3(key, map):
    global counter_t1
    lock = threading.Lock()
    for _ in range(10000):
        with lock:
            counter_t1 += 1
            map.put(key, counter_t1)

def task4(key, map):
    map.put(key, 0)
    for _ in range(10000):
        current_count = map.get(key)
        map.put(key, current_count + 1)

def task5(key, map):
    if not map.contains_key(key):
        map.put(key, 0)
    for _ in range(10000):
        map.lock(key)
        try:
            updated_count = map.get(key) + 1
            map.put(key, updated_count)
        finally:
            map.unlock(key)

def task6(key, map):
    if not map.contains_key(key):
        map.put(key, 0)
    for _ in range(10000):
        while True:
            old_val = map.get(key)
            new_val = old_val + 1
            if map.replace_if_same(key, old_val, new_val):
                break

def task7(key, hz):
    atomic_counter = hz.cp_subsystem.get_atomic_long(key).blocking()
    for _ in range(10000):
        atomic_counter.add_and_get(1)

def main():
    hz = hazelcast.HazelcastClient(cluster_name='OZ_lab1')
    map = hz.get_map('my-distributed-map').blocking()

    tasks = [[task3, 'task3', map], [task4, 'task4', map], [task5, 'task5', map], [task6, 'task6', map], [task7, 'task7', hz]]

    for task in tasks:
        print(f'///  {task[1]} ///')
        start_time = time.time()

        threads = [threading.Thread(target=task[0], args=[task[1], task[2]]) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        print(f'Execution time: {time.time() - start_time}')

        if task[1] == 'task7':
            atomic_counter = hz.cp_subsystem.get_atomic_long(task[1]).blocking()
            print(f'Final count: {atomic_counter.get()}')
        else:
            print(f'Final count: {map.get(task[1])}')

    hz.shutdown()

if __name__ == "__main__":
    main()