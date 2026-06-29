"""
app/workers/schedules/beat_schedule.py

Reference file — the actual beat schedule is defined in app/core/celery.py
(beat_schedule dict inside celery_app.conf.update).

This file documents the schedule for quick reference:

┌─────────────────────────────────────────────────────────────────────┐
│ Task                          │ Schedule          │ Queue           │
├─────────────────────────────────────────────────────────────────────┤
│ validate_all_catalogues       │ Mon 3am IST       │ catalogue       │
│ cleanup_expired_records       │ Daily 2am IST     │ cleanup         │
│ send_weekly_revenue_reports   │ Sun 11pm IST      │ notifications   │
│ check_stalled_playback        │ Every hour        │ playback        │
└─────────────────────────────────────────────────────────────────────┘

To add a new scheduled task:
  1. Write the task function in the appropriate tasks/ file
  2. Add it to beat_schedule in app/core/celery.py
  3. Update this reference table

To test a scheduled task manually:
  celery -A app.core.celery.celery_app call <task.name>
"""
