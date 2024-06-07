import os
import django
import random
from faker import Faker
from decimal import Decimal
from uuid import uuid4

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User
from store.models import Category, Discount, Book, BookImage, Customer, Address, Comment

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

# Create 1000 book images
for _ in range(1000):
    book = random.choice(books)
    book_image = BookImage(
        image=fake.image_url(),
        book=book
    )
    book_image.save()

# Create 200 users and customers
users = []
customers = []
for _ in range(200):
    user = User.objects.create_user(
        username=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),  # Email is included here
        password='password123'
    )
    users.append(user)
    customer = Customer(
        user=user,
        phone=fake.bothify(text='###########'),  # Generate a phone number with exactly 11 digits
        birth_date=fake.date_of_birth()
    )
    customer.save()
    customers.append(customer)

# Create addresses for customers
for customer in customers:
    address = Address(
        customer=customer,
        province=fake.state(),
        city=fake.city(),
        street=fake.street_address(),
        detail=fake.text(max_nb_chars=200)
    )
    address.save()

# Create comments for books
for _ in range(1000):
    book = random.choice(books)
    comment = Comment(
        body=fake.text(max_nb_chars=200),
        book=book,
        status=random.choice([Comment.COMMENT_STATUS_WAITING, Comment.COMMENT_STATUS_APPROVED, Comment.COMMENT_STATUS_NOT_APPROVED])
    )
    comment.save()
