from django.urls import path

from .views import product_list_api, banners_list_api, OrderAPIView
from .views import OrderAPIView

app_name = "foodcartapp"

urlpatterns = [
    path('products/', product_list_api),
    path('banners/', banners_list_api),
    path('order/', OrderAPIView.as_view(), name='order'),
]
