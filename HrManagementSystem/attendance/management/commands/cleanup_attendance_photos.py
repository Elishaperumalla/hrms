from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import Attendance


class Command(BaseCommand):
    help = "Delete attendance and pending photos older than five days."

    def handle(self, *args, **options):
        cutoff_date = timezone.localdate() - timedelta(days=5)
        deleted_recorded = 0
        deleted_pending = 0
        errors = 0

        records = Attendance.objects.filter(date__lt=cutoff_date).iterator()

        for attendance in records:
            changed_fields = []

            for field_name in ("check_in_photo", "check_out_photo"):
                photo = getattr(attendance, field_name)

                if not photo or not photo.name:
                    continue

                try:
                    photo.storage.delete(photo.name)
                    setattr(attendance, field_name, "")
                    changed_fields.append(field_name)
                    deleted_recorded += 1
                except (OSError, ValueError) as exc:
                    errors += 1
                    self.stderr.write(
                        f"Could not delete {photo.name}: {exc}"
                    )

            if changed_fields:
                attendance.save(update_fields=changed_fields)

        pending_dir = Path(settings.ATTENDANCE_PRIVATE_ROOT) / "pending"
        cutoff_timestamp = timezone.now().timestamp() - (
            5 * 24 * 60 * 60
        )

        if pending_dir.is_dir():
            for path in pending_dir.rglob("*"):
                if not path.is_file():
                    continue

                try:
                    if path.stat().st_mtime < cutoff_timestamp:
                        path.unlink()
                        deleted_pending += 1
                except OSError as exc:
                    errors += 1
                    self.stderr.write(f"Could not delete {path}: {exc}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup complete. Attendance photos deleted: "
                f"{deleted_recorded}; pending photos deleted: "
                f"{deleted_pending}; errors: {errors}."
            )
        )
