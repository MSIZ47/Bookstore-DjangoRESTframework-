from uuid import uuid4
from django.db import models
from django.conf import settings
from django.contrib import admin



class Category(models.Model):
    title = models.CharField(max_length=225)
    featured_book = models.ForeignKey('Book', on_delete=models.SET_NULL, related_name='+', null=True, blank=True)

    def __str__(self) -> str:
        return self.title

class Discount(models.Model):
    amount = models.FloatField()
    description = models.TextField()

    def __str__(self) -> str:
        return str(self.amount)


class Book(models.Model):
    title = models.CharField(max_length=225)
    slug = models.SlugField()
    description = models.TextField()
    price = models.DecimalField(max_digits=6,decimal_places=2)
    inventory = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='books')
    discount = models.ManyToManyField(Discount, blank=True, related_name='books')
    date_time_created = models.DateTimeField(auto_now_add=True)
    date_time_modified = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class BookImage(models.Model):
    image = models.ImageField(upload_to='store/images', null=True, blank=True)    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images')


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=11)
    birth_date = models.DateField(null= True,blank=True)

    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name

    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'


class Address(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, primary_key=True, related_name='address')
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    detail = models.TextField()


class Cart(models.Model):
    cart_id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='items_added')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    quantity = models.SmallIntegerField()


class Order(models.Model):
    ORDER_STATUS_PENDING = 'P'
    ORDER_STATUS_COMPLETE = 'C'
    ORDER_STATUS_FAILED = 'F'

    ORDER_STATUS = [
        (ORDER_STATUS_PENDING,'Pending'),
        (ORDER_STATUS_COMPLETE,'Complete'),
        (ORDER_STATUS_FAILED,'Failed'),
    ]
    status = models.CharField(max_length=1, choices=ORDER_STATUS, default=ORDER_STATUS_PENDING)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')

class OrderItem(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='items_ordered')
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6,decimal_places=2)
    date_time_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['order', 'book']]



class Comment(models.Model):
    COMMENT_STATUS_WAITING= 'W'
    COMMENT_STATUS_APPROVED = 'A'
    COMMENT_STATUS_NOT_APPROVED = 'N'

    COMMENT_STATUS = [
        (COMMENT_STATUS_WAITING,'Waiting'),
        (COMMENT_STATUS_APPROVED,'Approved'),
        (COMMENT_STATUS_NOT_APPROVED, 'NotApproved'),
    ]
    body = models.TextField()
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    date_was_sent = models.DateField(auto_now_add=True)
    date_was_placed = models.DateField(auto_now=True)
    status = models.CharField(max_length=1, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING)
















