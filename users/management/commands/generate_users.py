import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Alexander", "Debra",
    "Patrick", "Rachel", "Frank", "Carolyn", "Raymond", "Janet", "Jack", "Maria",
    "Dennis", "Olivia", "Jerry", "Heather", "Tyler", "Diane", "Aaron", "Julie",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
    "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
    "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward",
]


class Command(BaseCommand):
    help = "Generate users with unique usernames."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=610,
            help="Number of users to generate (default: 710).",
        )
        parser.add_argument(
            "--password",
            default="password123",
            help="Password assigned to every generated user (default: password123).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        rng = random.Random(610)  # deterministic runs

        existing = set(User.objects.values_list("username", flat=True))
        used = set(existing)

        password = make_password = options["password"]
        hashed = None

        users = []
        while len(users) < count:
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            base = f"{first.lower()}.{last.lower()}"

            username = base
            suffix = 0
            while username in used:
                suffix += 1
                username = f"{base}{suffix}"
            used.add(username)

            user = User(
                username=username,
                first_name=first,
                last_name=last,
                email=f"{username}@example.com",
            )
            if hashed is None:
                user.set_password(password)
                hashed = user.password  # hash once, reuse for speed
            else:
                user.password = hashed
            users.append(user)

        User.objects.bulk_create(users, batch_size=500)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(users)} users with unique usernames "
                f"(password: '{password}')."
            )
        )