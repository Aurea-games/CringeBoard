import os
import time


def main():
    interval = int(os.getenv("SCHEDULER_INTERVAL", "60"))
    print("Scheduler started. Interval:", interval, "seconds", flush=True)
    while True:
        # Placeholder for feed aggregation task
        print("[scheduler] tick", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()

