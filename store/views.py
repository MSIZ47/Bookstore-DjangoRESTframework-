from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action, permission_classes
from .models import *
from . import serializers
from .serializers import CustomerSerializer, AddressSerializer
from .pagination import DefaultPagination
from rest_framework.mixins import RetrieveModelMixin,CreateModelMixin,DestroyModelMixin,ListModelMixin
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from django.db.models import Prefetch
from .permissions import IsAdminOrReadOnly, IsSelfOrAdmin
from django_filters.rest_framework import DjangoFilterBackend
from .filters import BookFilter
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied


class BookViewSet(ModelViewSet):
    queryset = Book.objects.select_related('category').prefetch_related('images').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookFilter
    search_fields = ['title',]
    ordering_fields = ['price', 'date_time_modified']
    serializer_class = serializers.BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def destroy(self, request, *args, **kwargs):
        book_id = self.kwargs['pk']
        if OrderItem.objects.filter(book_id=book_id).exists():
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)
    
    pagination_class = DefaultPagination

class BookImageViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    def get_queryset(self):
        return BookImage.objects.filter(book_id=self.kwargs['book_pk'])
    
    serializer_class = serializers.BookImageSerializer

    def get_serializer_context(self):
        return {'book_id': self.kwargs['book_pk']}
    

class CommentViewSet(ModelViewSet):
    def get_queryset(self):
        return Comment.objects.select_related('book').filter(book_id = self.kwargs['book_pk'])
    
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = DefaultPagination
    
    def get_serializer_context(self):
        return {'book_id': self.kwargs['book_pk']}
    


class CategoryViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    def get_queryset(self):
        return Category.objects.prefetch_related('books').all()
    
    serializer_class = serializers.CategorySerializer

    pagination_class = DefaultPagination

    def destroy(self, request, *args, **kwargs):
        if Category.objects.values('books').count() > 0 :
            return Response({'error':'this category has one or more book in it.delete books first!'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

from rest_framework.permissions import IsAdminUser, IsAuthenticated

class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        return Customer.objects.select_related('user', 'address').all()

    # Restrict create and individual customer retrieval (retrieve action) to admins only
    def get_permissions(self):
        if self.action == 'list':  # Only admins can access /store/customers
            return [IsAdminUser()]
        elif self.action in ['retrieve']:  # Only admins can access /store/customers/1
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:  # Admins can update or delete customers
            return [IsAdminUser()]
        elif self.action == 'me':  # Authenticated users can access /store/customers/me
            return [IsAuthenticated()]
        return super().get_permissions()

    # Block creation of customers
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST', detail='Customer creation is not allowed.')

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        try:
            customer = Customer.objects.get(user_id=request.user.id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = CustomerSerializer(instance=customer, data=request.data, context={'customer_id': customer.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)



class AddressViewSet(ModelViewSet):
    serializer_class = AddressSerializer

    def get_queryset(self):
        # Ensure only admins can access /store/customers/<id>/address
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can access this endpoint.")
        return Address.objects.filter(customer_id=self.kwargs['customer_pk'])

    def get_permissions(self):
        # Block address creation (POST) for everyone
        if self.action == 'create':
            raise MethodNotAllowed("POST", detail="Address creation is not allowed.")
        
        # Allow only admins to access /store/customers/<id>/address
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        
        return [IsAuthenticated()]

    def get_serializer_context(self):
        return {'customer_id': self.kwargs['customer_pk']}
    


class DiscountViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Discount.objects.prefetch_related('books').all()
    serializer_class = serializers.DiscountSerializer
    pagination_class  = DefaultPagination


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get','patch','post', 'delete']

    def get_queryset(self):
        return CartItem.objects.select_related('book').filter(cart_id=self.kwargs['cart_pk'])
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateCartItemSerializer
        elif self.request.method == 'PATCH':
            return serializers.UpdateCartItemSerializer
        return serializers.CartItemSerializer
    
    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}
    

class CartViewSet(GenericViewSet,
                  CreateModelMixin,
                  DestroyModelMixin,
                  RetrieveModelMixin):
    permission_classes = [IsAuthenticated]
    queryset = Cart.objects.prefetch_related('items__book').all()
    serializer_class = serializers.CartSerializer



class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Order.objects.prefetch_related(
            Prefetch(
                'orderitems',
                queryset=OrderItem.objects.select_related('book'),
            )
        ).select_related('customer__user').all()

        user = self.request.user

        if user.is_staff:
            return queryset
        
        return queryset.filter(customer__user_id=user.id)    

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return serializers.UpdateOrderSerializer
        return serializers.OrderSerializer
    
    
    def create(self, request, *args, **kwargs):
        serializer = serializers.CreateOrderSerializer(data=request.data, context={'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = serializers.OrderSerializer(order)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        return Response({'eror':'Orders can not be Deleted!'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
