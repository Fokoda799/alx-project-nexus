import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone

from audiobooks.models import Audiobook, Author, Narrator, Genre 


class Command(BaseCommand):
    help = "Seed database with audiobooks, authors, narrators, and genres"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing data before seeding",
        )

    def handle(self, *args, **options):
        fake = Faker()

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            Audiobook.objects.all().delete()
            Author.objects.all().delete()
            Narrator.objects.all().delete()
            Genre.objects.all().delete()

        self.stdout.write(self.style.NOTICE("Creating authors..."))
        authors = [
            Author.objects.create(
                name=fake.name(),
                bio=fake.text(max_nb_chars=300),
                photo=f"https://picsum.photos/seed/author{n}/400/400",
                social_links={}
            )
            for n in range(50)
        ]

        self.stdout.write(self.style.NOTICE("Creating narrators..."))
        narrators = [
            Narrator.objects.create(
                name=fake.name(),
                bio=fake.text(max_nb_chars=200),
                photo=f"https://picsum.photos/seed/narrator{n}/400/400",
                social_links={}
            )
            for n in range(50)
        ]

        self.stdout.write(self.style.NOTICE("Creating genres..."))
        genres = [
            Genre.objects.create(
                name=fake.word().capitalize(),
                description=fake.sentence()
            )
            for _ in range(20)
        ]

        self.stdout.write(self.style.NOTICE("Creating audiobooks..."))
        for _ in range(200):
            book = Audiobook.objects.create(
                title=fake.sentence(nb_words=2),
                description=fake.paragraph(nb_sentences=5),
                cover_image=f"https://picsum.photos/seed/book{random.randint(1,9999)}/600/900",
                audio_file="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                duration_seconds=random.randint(1800, 20000),
                release_date=fake.date_between(start_date="-10y", end_date="today"),
                language=random.choice(["English", "Arabic", "French", "Spanish"]),
                publisher=fake.company(),
                isbn = fake.isbn13().replace("-", ""),
            )

            # Add random authors
            book.authors.add(*random.sample(authors, random.randint(1, 3)))

            # Add random narrators
            book.narrators.add(*random.sample(narrators, random.randint(1, 2)))

            # Add random genres
            book.genres.add(*random.sample(genres, random.randint(1, 2)))

        self.stdout.write(self.style.SUCCESS("🎉 Database seeded successfully!"))
