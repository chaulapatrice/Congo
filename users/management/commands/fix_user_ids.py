import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from users.models import User
from django.db import transaction


class Command(BaseCommand):
    help = "Fix user IDs to match the correct dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="updated_users.csv",
            help="Input CSV path (default: updated_users.csv).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                user = User.objects.get(id=row["current_id"])
                user.id = row["new_id"]
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Fixed ID for {user.username}"))

        self.stdout.write(self.style.SUCCESS(f"Fixed user IDs"))