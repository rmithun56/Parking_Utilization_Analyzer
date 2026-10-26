from datetime import datetime
import csv
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "mithun@sql12",
    "database": "parking_analyzer"
}


def connect_db():
    return mysql.connector.connect(**DB_CONFIG)


def choose_area(cursor):
    cursor.execute(
        "SELECT area_id, area_name, capacity FROM parking_areas ORDER BY area_name"
    )
    areas = cursor.fetchall()
    print("\nParking areas:")
    for area_id, name, capacity in areas:
        print(f"{area_id}. {name} (capacity: {capacity})")
    try:
        return int(input("Enter area ID: ").strip())
    except ValueError:
        print("Area ID must be a number.")
        return None


def record_entry():
    vehicle_id = input("Vehicle registration ID: ").strip().upper()
    if not vehicle_id:
        print("Vehicle ID cannot be empty.")
        return

    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT transaction_id FROM parking_transactions
               WHERE vehicle_id=%s AND exit_time IS NULL""",
            (vehicle_id,)
        )
        if cur.fetchone():
            print("This vehicle already has an active parking entry.")
            return

        area_id = choose_area(cur)
        if area_id is None:
            return

        cur.execute("SELECT capacity FROM parking_areas WHERE area_id=%s",
                    (area_id,))
        area = cur.fetchone()
        if area is None:
            print("Parking area not found.")
            return

        cur.execute(
            """SELECT COUNT(*) FROM parking_transactions
               WHERE area_id=%s AND exit_time IS NULL""",
            (area_id,)
        )
        occupied = cur.fetchone()[0]
        if occupied >= area[0]:
            print("This parking area is full.")
            return

        cur.execute(
            """INSERT INTO parking_transactions
               (vehicle_id, area_id, entry_time)
               VALUES (%s, %s, %s)""",
            (vehicle_id, area_id, datetime.now())
        )
        conn.commit()
        print("Entry recorded successfully.")
    finally:
        conn.close()


def record_exit():
    vehicle_id = input("Vehicle registration ID: ").strip().upper()
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT transaction_id, entry_time FROM parking_transactions
               WHERE vehicle_id=%s AND exit_time IS NULL
               ORDER BY entry_time DESC LIMIT 1""",
            (vehicle_id,)
        )
        row = cur.fetchone()
        if row is None:
            print("No active parking transaction found.")
            return

        transaction_id, entry_time = row
        exit_time = datetime.now()
        duration = max(0, (exit_time - entry_time).total_seconds() / 3600)

        cur.execute(
            """UPDATE parking_transactions
               SET exit_time=%s, duration_hours=%s
               WHERE transaction_id=%s""",
            (exit_time, round(duration, 2), transaction_id)
        )
        conn.commit()
        print(f"Exit recorded. Parking duration: {duration:.2f} hours.")
    finally:
        conn.close()


def show_records():
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT t.transaction_id, t.vehicle_id, p.area_name,
                      t.entry_time, t.exit_time, t.duration_hours
               FROM parking_transactions t
               JOIN parking_areas p ON p.area_id=t.area_id
               ORDER BY t.entry_time DESC"""
        )
        rows = cur.fetchall()
        print("\nID | Vehicle | Area | Entry | Exit | Duration (hours)")
        for row in rows:
            print(" | ".join(str(value) if value is not None else "-"
                             for value in row))
        if not rows:
            print("No transactions recorded.")
    finally:
        conn.close()


def utilization_report():
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT p.area_name, p.capacity,
                      COUNT(t.transaction_id) AS occupied
               FROM parking_areas p
               LEFT JOIN parking_transactions t
                 ON p.area_id=t.area_id AND t.exit_time IS NULL
               GROUP BY p.area_id, p.area_name, p.capacity
               ORDER BY p.area_name"""
        )
        print("\nArea | Capacity | Occupied | Available | Utilization | Category")
        for name, capacity, occupied in cur.fetchall():
            available = max(0, capacity - occupied)
            percent = (occupied / capacity) * 100
            if percent <= 30:
                category = "UNDERUTILIZED"
            elif percent <= 70:
                category = "NORMAL"
            elif percent <= 90:
                category = "HIGH"
            else:
                category = "OVERLOADED"
            print(f"{name} | {capacity} | {occupied} | {available} | "
                  f"{percent:.1f}% | {category}")
    finally:
        conn.close()


def peak_hour_report():
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT HOUR(entry_time) AS entry_hour, COUNT(*) AS total
               FROM parking_transactions
               GROUP BY HOUR(entry_time)
               ORDER BY total DESC, entry_hour"""
        )
        rows = cur.fetchall()
        if not rows:
            print("No records available for peak-hour analysis.")
            return
        print("\nHour | Number of vehicle entries")
        for hour, count in rows:
            print(f"{hour:02d}:00 | {count}")
        print(f"Peak entry hour: {rows[0][0]:02d}:00 ({rows[0][1]} entries)")
    finally:
        conn.close()


def export_csv():
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT t.transaction_id, t.vehicle_id, p.area_name,
                      t.entry_time, t.exit_time, t.duration_hours
               FROM parking_transactions t
               JOIN parking_areas p ON p.area_id=t.area_id
               ORDER BY t.entry_time"""
        )
        rows = cur.fetchall()
        with open("parking_report.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Transaction ID", "Vehicle ID", "Area",
                             "Entry Time", "Exit Time", "Duration Hours"])
            writer.writerows(rows)
        print(f"Exported {len(rows)} records to parking_report.csv.")
    finally:
        conn.close()


def main():
    actions = {
        "1": ("Record vehicle entry", record_entry),
        "2": ("Record vehicle exit", record_exit),
        "3": ("View parking records", show_records),
        "4": ("Parking-area utilization", utilization_report),
        "5": ("Peak-hour analysis", peak_hour_report),
        "6": ("Export report to CSV", export_csv)
    }
    while True:
        print("\n=== PARKING UTILIZATION ANALYZER ===")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        print("0. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye.")
            break
        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Try again.")
            continue
        try:
            action[1]()
        except Error as exc:
            print("Database error:", exc)
        except (OSError, ValueError) as exc:
            print("Operation error:", exc)


if __name__ == "__main__":
    main()
