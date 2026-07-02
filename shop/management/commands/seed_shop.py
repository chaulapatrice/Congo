import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Category, Product

# Category name -> list of representative product nouns used to build names.
CATEGORY_SEED = {
    "Electronics": ["Laptop", "Smartphone", "Headphones", "Monitor", "Keyboard", "Mouse", "Tablet", "Charger"],
    "Books": ["Novel", "Cookbook", "Biography", "Textbook", "Comic", "Journal", "Dictionary", "Guide"],
    "Home & Kitchen": ["Blender", "Toaster", "Cookware Set", "Knife", "Mug", "Lamp", "Cushion", "Kettle"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Hoodie", "Socks", "Cap"],
    "Sports & Outdoors": ["Tent", "Dumbbell", "Yoga Mat", "Bicycle", "Backpack", "Water Bottle", "Ball", "Gloves"],
    "Toys & Games": ["Puzzle", "Board Game", "Action Figure", "Building Blocks", "Doll", "RC Car", "Card Game", "Plush"],
    "Beauty & Health": ["Shampoo", "Moisturizer", "Perfume", "Vitamins", "Sunscreen", "Lipstick", "Razor", "Serum"],
    "Grocery": ["Coffee", "Olive Oil", "Pasta", "Tea", "Chocolate", "Honey", "Cereal", "Spices"],
    "Automotive": ["Car Cover", "Dash Cam", "Tire Gauge", "Floor Mats", "Air Freshener", "Jump Starter", "Wax", "Phone Mount"],
    "Office Supplies": ["Notebook", "Pen Set", "Stapler", "Desk Organizer", "Whiteboard", "Folder", "Marker", "Calculator"],
}

ADJECTIVES = [
    "Premium", "Classic", "Deluxe", "Eco", "Smart", "Portable", "Compact",
    "Pro", "Ultra", "Essential", "Vintage", "Modern", "Heavy-Duty", "Lightweight",
]

BRANDS = [
    "Acme", "Zenith", "Nova", "Pulse", "Apex", "Vertex", "Lumina",
    "Orbit", "Cascade", "Summit", "Nimbus", "Forge",
]


class Command(BaseCommand):
    help = "Generate sample categories and products for the shop."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            type=int,
            default=2000,
            help="Number of products to generate (default: 2000).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing products and categories before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        total_products = options["products"]

        if options["clear"]:
            self.stdout.write("Clearing existing products and categories...")
            Product.objects.all().delete()
            Category.objects.all().delete()

        categories = self._create_categories()
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(categories)} categories."))

        self._create_products(total_products, categories)
        self.stdout.write(
            self.style.SUCCESS(f"Generated {total_products} products.")
        )

    def _create_categories(self):
        categories = {}
        for name in CATEGORY_SEED:
            category, _ = Category.objects.get_or_create(name=name)
            categories[name] = category
        return categories

    def _create_products(self, total, categories):
        category_names = list(categories)
        batch_size = 500

        created_ids = []
        batch = []
        # Store the intended category assignment per product for the M2M pass.
        assignments = []

        for i in range(total):
            primary_name = random.choice(category_names)
            noun = random.choice(CATEGORY_SEED[primary_name])
            name = f"{random.choice(BRANDS)} {random.choice(ADJECTIVES)} {noun}"
            price = Decimal(f"{random.uniform(4.99, 1999.99):.2f}")
            description = (
                f"The {name} is a top-quality {noun.lower()} from the "
                f"{primary_name} range. Reliable, well-designed, and built to last."
            )
            product = Product(name=name, description=description, price=price)
            batch.append(product)

            # 1-3 categories, always including the primary one.
            extra = random.sample(
                [n for n in category_names if n != primary_name],
                k=random.randint(0, 2),
            )
            assignments.append([primary_name, *extra])

            if len(batch) >= batch_size:
                created_ids.extend(self._flush_batch(batch))
                batch = []

        if batch:
            created_ids.extend(self._flush_batch(batch))

        # Attach categories via the through model in bulk.
        self._attach_categories(created_ids, assignments, categories)

    def _flush_batch(self, batch):
        created = Product.objects.bulk_create(batch)
        return [p.pk for p in created]

    def _attach_categories(self, product_ids, assignments, categories):
        through = Product.categories.through
        links = []
        for product_id, names in zip(product_ids, assignments):
            for name in names:
                links.append(
                    through(
                        product_id=product_id,
                        category_id=categories[name].pk,
                    )
                )
        through.objects.bulk_create(links, batch_size=1000, ignore_conflicts=True)