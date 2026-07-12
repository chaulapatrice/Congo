from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("products/<int:pk>/review/", views.add_review, name="add_review"),
]