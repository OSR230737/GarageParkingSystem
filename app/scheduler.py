from apscheduler.schedulers.background import BackgroundScheduler

from app.clock import checkout_overdue_sessions
from app.db import SessionLocal

scheduler = BackgroundScheduler()


def run_scheduled_clock() -> None:
    db = SessionLocal()
    try:
        checked_out = checkout_overdue_sessions(db)
        if checked_out:
            print(f"Scheduled clock checked out {len(checked_out)} session(s)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        run_scheduled_clock,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily-clock",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
