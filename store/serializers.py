from rest_framework import serializers
from .models import *
from django.db import transaction

class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookImage
        fields = ['id', 'image']
    
    def create(self, validated_data):
        book_id = self.context['book_id']
        return BookImage.objects.create(book_id=book_id, **validated_data)
    

class BookSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    images = BookImageSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title','slug', 'images', 'description', 'price','inventory', 'category']


class SimpleBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id','title', 'price']


class CommentSerializer(serializers.ModelSerializer):
    book = serializers.StringRelatedField()

    class Meta:
        model = Comment
        fields = ['id', 'body', 'book','date_was_placed']

    def create(self, validated_data):
        book_id = self.context['book_id']
        return Comment.objects.create(book_id=book_id, **validated_data)



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title', 'books_count']

    books_count = serializers.SerializerMethodField(read_only=True)

    def get_books_count(self, category):
        return category.books.count()
    
class SimpleAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['province', 'city', 'street', 'detail']


class AddressSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only=True)  # To display customer in a readable format

    class Meta:
        model = Address
        fields = ['customer_id', 'customer', 'province', 'city', 'street', 'detail']
        extra_kwargs = {'customer_id': {'read_only': True}}  # customer_id should not be writable

    def create(self, validated_data):
        # Get customer_id from context
        customer_id = self.context.get('customer_id')

        # Ensure customer_id is present in the context
        if not customer_id:
            raise serializers.ValidationError("Customer ID is required.")

        # Fetch the customer instance
        customer = Customer.objects.get(id=customer_id)

        # Prevent creating multiple addresses for the same customer
        if hasattr(customer, 'address'):
            raise serializers.ValidationError("Address already exists for this customer.")

        # Set customer and create address
        validated_data['customer'] = customer
        return Address.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Update address fields
        instance.province = validated_data.get('province', instance.province)
        instance.city = validated_data.get('city', instance.city)
        instance.street = validated_data.get('street', instance.street)
        instance.detail = validated_data.get('detail', instance.detail)

        # Save the updated address
        instance.save()
        return instance

        
class CustomerSerializer(serializers.ModelSerializer):
    address = AddressSerializer()  # Use AddressSerializer to handle address data

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'address']
        read_only_fields = ['user_id']

    def update(self, instance, validated_data):
        # Extract address data if present in the request
        address_data = validated_data.pop('address', None)

        # Handle address create or update
        if address_data:
            # Check if the customer already has an address
            if hasattr(instance, 'address'):
                # Update existing address
                address_serializer = AddressSerializer(instance=instance.address, data=address_data, context={'customer_id': instance.id})
            else:
                # Create a new address if the customer doesn't have one
                address_serializer = AddressSerializer(data=address_data, context={'customer_id': instance.id})

            # Validate and save the address
            address_serializer.is_valid(raise_exception=True)
            address_serializer.save()

        # Update the customer data (phone, birth_date)
        return super().update(instance, validated_data)








class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'amount', 'description', 'books']

    books = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), many=True)


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id','book','quantity','total_price']

    book = SimpleBookSerializer()    
    total_price = serializers.SerializerMethodField(read_only=True)

    def get_total_price(self, item):
        return item.book.price * item.quantity


class CreateCartItemSerializer(serializers.ModelSerializer):
    book_id = serializers.IntegerField()
    class Meta:
        model = CartItem
        fields = ['id','book_id', 'quantity']

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        book_id = self.validated_data['book_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, book_id=book_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id,
                                                **self.validated_data)
            return self.instance
    

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['cart_id', 'items', 'total_price']

    cart_id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart:Cart):
        return sum([item.book.price * item.quantity for item in cart.items.all()])
    


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'quantity', 'unit_price']

    book = SimpleBookSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'orderitems', 'status', 'customer']
    orderitems = OrderItemSerializer(many=True)


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']



class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('NO cart with the given ID!')
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('Cart is Empty.')
        return cart_id
    
    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']

            customer = Customer.objects.select_related('user').get(user_id = self.context['user_id'])

            order = Order()
            order.customer = customer
            order.save()

            cart_items = CartItem.objects.select_related('book').filter(cart_id=cart_id)

            order_items = [
                OrderItem(
                order=order,
                book = item.book,
                quantity = item.quantity,
                unit_price = item.book.price
            
            )for item in cart_items ]

            OrderItem.objects.bulk_create(order_items)

            Cart.objects.filter(cart_id=cart_id).delete()

            return order