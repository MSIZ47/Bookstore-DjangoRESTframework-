from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()
router.register('books',views.BookViewSet, basename='books')
router.register('categories', views.CategoryViewSet, basename='categories')
router.register('discounts', views.DiscountViewSet, basename='discounts')
router.register('customers', views.CustomerViewSet, basename='customers')
router.register('carts', views.CartViewSet, basename='carts')
router.register('orders', views.OrderViewSet, basename='orders')



book_router = routers.NestedDefaultRouter(router, 'books', lookup='book')
book_router.register('images', views.BookImageViewSet, basename='book-images')
book_router.register('comments', views.CommentViewSet, basename='book-comments')

customer_router = routers.NestedDefaultRouter(router, 'customers', lookup='customer')
customer_router.register('address', views.AddressViewSet, basename='customer_address')

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_router.register('items', views.CartItemViewSet, basename='cart-items')

urlpatterns = router.urls + book_router.urls + customer_router.urls + cart_router.urls