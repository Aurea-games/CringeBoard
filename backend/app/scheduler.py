import time

from app.core.config import get_settings


def main():
    settings = get_settings()
    interval = settings.scheduler_interval
    print("Scheduler started. Interval:", interval, "seconds", flush=True)
    while True:
        # Placeholder for feed aggregation task
        print("[scheduler] tick", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
