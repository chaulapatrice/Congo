import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from shop.models import Product
from django.db import transaction


class Command(BaseCommand):
    help = "Export products to a CSV file (name, category, price, description)."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="updated_products.csv",
            help="Input CSV path (default: updated_products.csv).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                product = Product.objects.get(id=row["current_id"])
                product.categories.all().delete()
                product.id = row["new_id"]
                product.save()
                category = product.categories.create(name=row["category"])
                product.categories.add(category)
                self.stdout.write(self.style.SUCCESS(f"Fixed ID for {product.name}"))

        self.stdout.write(self.style.SUCCESS(f"Fixed products IDs"))