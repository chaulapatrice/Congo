import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from shop.models import Product,  Rating
from users.models import User
from django.db import transaction


class Command(BaseCommand):
    help = "Create product ratings from ratings.csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="ratings.csv",
            help="Input CSV path (default: ratings.csv).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                product = Product.objects.get(id=row["productId"])
                user = User.objects.get(id=row["userId"])

                if not Rating.objects.filter(product=product, user=user).exists():
                    Rating.objects.create(product=product, user=user, rating=int(float(row["rating"])))
                    self.stdout.write(self.style.SUCCESS(f"Created rating for product: {product.name}, user: {user.username}"))

        self.stdout.write(self.style.SUCCESS(f"Seeded ratings"))