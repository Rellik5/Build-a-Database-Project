import sys
from hashtable import HashTable
from persistence import Log
from store import new_string, new_hash, STRING, HASH

store = HashTable()
log = Log("data.db")


def apply_record(record):
    """Re-apply one logged record to memory. Does NOT write to the log."""
    action = record[0]
    if action == "SET":
        store.set(record[1], new_string(record[2]))
    elif action == "DEL":
        store.delete(record[1])
    elif action == "HSET":
        item = store.get(record[1])
        if item is None or item.vtype != HASH:
            item = new_hash()
            store.set(record[1], item)
        item.data.set(record[2], record[3])


log.replay(apply_record)   # rebuild state from last run
log.open_for_append()      # then start appending new writes

for line in sys.stdin:
    line = line.rstrip("\n")
    parts = line.split()
    if not parts:
        continue

    command = parts[0].upper()

    if command == "SET":
        key = parts[1]
        value = parts[2]
        store.set(key, new_string(value))
        log.append(["SET", key, value])
        print("OK")

    elif command == "GET":
        key = parts[1]
        item = store.get(key)
        if item is None:
            print("(nil)")
        elif item.vtype != STRING:
            print("ERR wrong type")
        else:
            print(item.data)

    elif command == "DEL":
        key = parts[1]
        removed = store.delete(key)
        if removed:
            log.append(["DEL", key])
            print("1")
        else:
            print("0")

    elif command == "EXISTS":
        key = parts[1]
        if store.get(key) is None:
            print("0")
        else:
            print("1")

    elif command == "INCR" or command == "DECR":
        key = parts[1]
        item = store.get(key)

        if item is None:
            number = 0
        elif item.vtype != STRING:
            print("ERR wrong type")
            continue
        else:
            try:
                number = int(item.data)
            except ValueError:
                print("ERR value is not an integer")
                continue

        if command == "INCR":
            number = number + 1
        else:
            number = number - 1

        store.set(key, new_string(str(number)))
        log.append(["SET", key, str(number)])
        print(number)

    elif command == "HSET":
        key = parts[1]
        field = parts[2]
        value = parts[3]
        item = store.get(key)

        if item is None:
            item = new_hash()           # first field -- create the hash
            store.set(key, item)
        elif item.vtype != HASH:
            print("ERR wrong type")
            continue

        item.data.set(field, value)     # item.data IS a HashTable
        log.append(["HSET", key, field, value])
        print("1")

    elif command == "HGET":
        key = parts[1]
        field = parts[2]
        item = store.get(key)

        if item is None:
            print("(nil)")
        elif item.vtype != HASH:
            print("ERR wrong type")
        else:
            value = item.data.get(field)
            if value is None:
                print("(nil)")
            else:
                print(value)

    elif command == "HGETALL":
        key = parts[1]
        item = store.get(key)

        if item is None:
            print("(empty)")
        elif item.vtype != HASH:
            print("ERR wrong type")
        else:
            found = False
            for field, value in item.data.items():
                print(field + ": " + value)
                found = True
            if not found:
                print("(empty)")

    elif command == "EXIT":
        break

    else:
        print("ERR unknown command")

log.close()