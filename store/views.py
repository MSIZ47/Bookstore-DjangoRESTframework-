from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import *
from . import serializers
from .pagination import DefaultPagination
from rest_framework.mixins import RetrieveModelMixin,CreateModelMixin,DestroyModelMixin
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from .filters import BookFilter


class BookViewSet(ModelViewSet):
    queryset = Book.objects.select_related('category').prefetch_related('images').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookFilter
    search_fields = ['title',]
    ordering_fields = ['price', 'date_time_modified']




    
    serializer_class = serializers.BookSerializer
    def get_serializer_context(self):
        return {'request': self.request}
    
    def destroy(self, request, *args, **kwargs):
        book_id = self.kwargs['pk']
        if OrderItem.objects.filter(book_id=book_id).exists():
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)
    
    pagination_class = DefaultPagination

class BookImageViewSet(ModelViewSet):
    def get_queryset(self):
        return BookImage.objects.filter(book_id=self.kwargs['book_pk'])
    
    serializer_class = serializers.BookImageSerializer

    def get_serializer_context(self):
        return {'book_id': self.kwargs['book_pk']}
    

class CommentViewSet(ModelViewSet):
    def get_queryset(self):
        return Comment.objects.select_related('book').filter(book_id = self.kwargs['book_pk'])
    
    serializer_class = serializers.CommentSerializer

    pagination_class = DefaultPagination
    
    def get_serializer_context(self):
        return {'book_id': self.kwargs['book_pk']}
    


class CategoryViewSet(ModelViewSet):
    def get_queryset(self):
        return Category.objects.prefetch_related('books').all()
    
    serializer_class = serializers.CategorySerializer

    pagination_class = DefaultPagination

    def destroy(self, request, *args, **kwargs):
        if Category.objects.values('books').count() > 0 :
            return Response({'error':'this category has one or more book in it.delete books first!'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

class CustomerViewSet(ModelViewSet):
    def get_queryset(self):
        return Customer.objects.select_related('user').prefetch_related('address').all()
    serializer_class = serializers.CustomerSerializer


class AddressViewSet(ModelViewSet):
    def get_queryset(self):
        return Address.objects.select_related('customer').filter(customer_id = self.kwargs['customer_pk'])
    serializer_class = serializers.AddressSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}
    


class DiscountViewSet(ModelViewSet):

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
