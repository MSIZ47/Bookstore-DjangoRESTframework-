from typing import Any
from django.contrib import admin, messages
from django.db.models.query import QuerySet
from django.http import HttpRequest
from .models import *
from django.utils.html import format_html
from django.utils.http import urlencode
from django.db.models.aggregates import Count
from django.urls import reverse



class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 0
    readonly_fields = ['thumbnail']


    def thumbnail(self , instance):
        if instance.image.name != '':
            return format_html(f'<img src ="{instance.image.url}" class ="thumbnail" />')
        return ''



class PriceFilter(admin.SimpleListFilter):
    title = 'price'
    parameter_name = 'low price'

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[Any, str]]:
        return [
            ('<100', 'low'),
            ('600>', 'high')
            ]

    def queryset(self, request: Any, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        if self.value() == '<100':
            return queryset.filter(price__lt=100)
        elif self.value() == '600>':
            return queryset.filter(price__gt=600)





@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'inventory_status', 'date_time_modified','category']
    list_per_page = 10
    list_editable = ['price']
    list_filter = ['category', PriceFilter]
    autocomplete_fields = ['category']
    prepopulated_fields = {'slug':['title']}
    search_fields = ['title']
    inlines = [BookImageInline]




    @admin.display(ordering='inventory')
    def inventory_status(self, product):
        if product.inventory < 10:
            return 'Low'
        return 'OK'
    

    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{updated_count} products were successfully updated.',
            messages.ERROR
        )

    class Media:
        css = {
            'all':['store/thumbnail.css']
        }

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'books_count']
    search_fields = ['title']
    autocomplete_fields = ['featured_book']

    @admin.display(ordering='books_count')
    def books_count(self, category):
        url = (
            reverse('admin:store_book_changelist')
            + '?'
            + urlencode({
                'category__id': str(category.id)
            }))
        return format_html('<a href="{}">{} Books</a>', url, category.books_count)
    
    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).annotate(books_count = Count('books'))
                        

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user','first_name','last_name','phone', 'birth_date', 'orders_count']
    list_select_related = ['user']
    search_fields = ['user__username']
    ordering = ['user__first_name', 'user__last_name']
    search_fields = ['first_name__istartswith', 'last_name__istartswith']

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).annotate(orders_count=Count('orders'))
    

    @admin.display(ordering='orders_count')
    def orders_count(self, customer):
        url = (reverse('admin:store_order_changelist')
        +'?'
        + urlencode({
            'customer__id': str(customer.id)
            }))
        return format_html('<a href="{}">{} Orders</a>', url, customer.orders_count)



class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ['book']
    min_num = 1
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'status']
    autocomplete_fields = ['customer']
    inlines = [OrderItemInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'province','city','street', 'detail']
    autocomplete_fields = ['customer']



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['body', 'book', 'status']
    autocomplete_fields = ['book']


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = [ 'image']