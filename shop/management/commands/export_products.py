import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from shop.models import Product


class Command(BaseCommand):
    help = "Export products to a CSV file (name, category, price, description)."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="exported_products.csv",
            help="Output CSV path (default: exported_products.csv).",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])

        products = Product.objects.prefetch_related("categories").order_by("name")

        count = 0
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["current_id", "name", "category", "price", "description"])
            for product in products.iterator(chunk_size=2000):
                category = product.categories.first().name if product.categories.exists() else "Uncategorized"
                writer.writerow([product.id, product.name, category, product.price, product.description])
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Exported {count} products to {path}."))