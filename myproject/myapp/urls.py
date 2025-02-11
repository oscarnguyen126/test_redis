from django.urls import path
from .views import create_product, get_product, update_product, delete_product,get_all_products_db,get_all_products_cache


urlpatterns = [
    path('products/db/', get_all_products_db, name='get_all_products_db'),
    path('products/cache/', get_all_products_cache, name='get_all_products_cache'),
    path('product/create/', create_product, name='create_product'),
    path('product/<int:product_id>/', get_product, name='get_product'),
    path('product/update/<int:product_id>', update_product, name='update_product'),
    path('product/delete/<int:product_id>', delete_product, name='delete_product'),
]
