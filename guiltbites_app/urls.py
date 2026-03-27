from django.urls import path 
from . import views

urlpatterns = [
    path('' , views.home),
    path('about_us' , views.about_us),
    path('contact_us' , views.contact_us),

    path('shop/categories' , views.shop_categories),
    path('shop/products/<int:category_id>' , views.shop_products),
    path('shop/product_details/<int:product_id>' , views.product_details),

    path('register' , views.register),
    path('log_in' , views.log_in),
    path('log_out' , views.log_out),

    path('cart' , views.cart),
    path('cart/add/<int:product_id>' , views.add_to_cart),
    path('cart/edit' , views.edit_quantity),
    path('cart/remove/<int:product_id>' , views.remove_from_cart),

    path('checkout' , views.checkout),
    path('orders' , views.user_orders, name='user_orders'),

    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    path('dashboard/add_category' , views.add_category),
    path('dashboard/edit_category/<int:category_id>' , views.edit_category),
    path('dashboard/delete_category/<int:category_id>' , views.delete_category),

    path('dashboard/add_product' , views.add_product),
    path('dashboard/edit_product/<int:product_id>' , views.edit_product),
    path('dashboard/delete_product/<int:product_id>' , views.delete_product),

    path('dashboard/orders' , views.manage_orders),
    path('dashboard/orders_update' , views.update_status),
    path('dashboard/orders_delete', views.delete_order),
    path('shop/go_to_custom_box/', views.custom_view),
    path('cart/add/custom_box', views.add_custom_box_to_cart, name='add_custom_box_to_cart'),

    path('shop/search_products/', views.search_products, name='search_products'),
    path('cart/add_ajax/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
]