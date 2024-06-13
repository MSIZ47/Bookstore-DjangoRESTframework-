import os
import django
import random
from faker import Faker
from decimal import Decimal
from uuid import uuid4

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Category, Discount, Book, Comment

fake = Faker()

# Create 20 categories
categories = []
for _ in range(20):
    category = Category(title=fake.word())
    category.save()
    categories.append(category)

# Create 50 discounts
discounts = []
for _ in range(50):
    discount = Discount(
        amount=fake.random_number(digits=2),
        description=fake.text(max_nb_chars=100)
    )
    discount.save()
    discounts.append(discount)

# Create 500 books
books = []
for _ in range(500):
    category = random.choice(categories)
    book = Book(
        title=fake.sentence(nb_words=5),
        slug=fake.slug(),
        description=fake.text(max_nb_chars=200),
        price=Decimal(fake.random_number(digits=5) / 100),
        inventory=fake.random_int(min=0, max=1000),
        category=category
    )
    book.save()
    book.discount.set(random.sample(discounts, k=random.randint(0, 5)))  # Add random discounts to the book
    books.append(book)
    
    # Optionally, set a featured book for the category
    if random.choice([True, False]):
        category.featured_book = book
        category.save()



# Create comments for books
for _ in range(1000):
    book = random.choice(books)
    comment = Comment(
        body=fake.text(max_nb_chars=200),
        book=book,
        status=random.choice([Comment.COMMENT_STATUS_WAITING, Comment.COMMENT_STATUS_APPROVED, Comment.COMMENT_STATUS_NOT_APPROVED])
    )
    comment.save()
