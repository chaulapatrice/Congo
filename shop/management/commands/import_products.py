import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from shop.models import Category, Product


class Command(BaseCommand):
    help = "Import products from a JSON file into the shop."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="products.json",
            help="Path to the products JSON file (default: products.json).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing products and categories before importing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {path}: {exc}")

        if not isinstance(data, list):
            raise CommandError("Expected the JSON root to be a list of products.")

        if options["clear"]:
            self.stdout.write("Clearing existing products and categories...")
            Product.objects.all().delete()
            Category.objects.all().delete()

        categories = {}  # name -> Category, cached to avoid repeated queries
        created = 0
        skipped = 0

        for index, item in enumerate(data):
            if not isinstance(item, dict):
                self.stderr.write(f"Skipping entry {index}: not an object.")
                skipped += 1
                continue

            name = (item.get("name") or "").strip()
            if not name:
                self.stderr.write(f"Skipping entry {index}: missing name.")
                skipped += 1
                continue

            try:
                price = Decimal(str(item.get("price", "0")))
            except (InvalidOperation, TypeError):
                self.stderr.write(f"Skipping '{name}': invalid price {item.get('price')!r}.")
                skipped += 1
                continue

            product, was_created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "description": item.get("description", ""),
                    "price": price,
                },
            )
            if not was_created:
                skipped += 1
                continue

            category_name = (item.get("category") or "").strip()
            if category_name:
                category = categories.get(category_name)
                if category is None:
                    category, _ = Category.objects.get_or_create(name=category_name)
                    categories[category_name] = category
                product.categories.add(category)

            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} products "
                f"({len(categories)} categories, {skipped} skipped)."
            )
        )