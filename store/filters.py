from unicodedata import category
from django_filters.rest_framework.filterset import FilterSet
from .models import Book


class BookFilter(FilterSet):
    class Meta:
        model = Book
        fields = {'category_id':['exact'],
                  'price':['gt','lt'],
                  'inventory':['gt','lt'],
                  }