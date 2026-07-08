import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    help = "Export users to a CSV file (current_id, username, first_name, last_name)."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="exported_users.csv",
            help="Output CSV path (default: exported_users.csv).",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])

        users = User.objects.all().order_by("id")

        count = 0
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["current_id", "username", "first_name", "last_name"])
            for user in users.iterator(chunk_size=2000):
                writer.writerow([user.id, user.username, user.first_name, user.last_name])
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Exported {count} users to {path}."))