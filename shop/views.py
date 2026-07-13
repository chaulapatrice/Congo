from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .forms import RatingForm
from .models import Category, Product, Rating
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import csv
from django.db import transaction
from users.models import User
from .models import Product


class ProductListView(ListView):
    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        return Product.objects.prefetch_related("categories").order_by("name")


class ProductDetailView(DetailView):
    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return response

    def get_queryset(self):
        return Product.objects.prefetch_related("categories", "ratings__user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        categories = product.categories.all()
        # Related products drawn from the same categories, excluding this one.
        related = (
            Product.objects.filter(categories__in=categories)
            .exclude(pk=product.pk)
            .distinct()
            .prefetch_related("categories")[:4]
        )
        context["related_products"] = related
        context["review_form"] = kwargs.get("review_form") or RatingForm()
        return context


@login_required
@require_POST
def add_review(request, pk):
    """Attach a review from the current user to the given product."""
    product = get_object_or_404(Product, pk=pk)

    if Rating.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "You have already reviewed this product.")
        return redirect("shop:product_detail", pk=product.pk)

    form = RatingForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, "Thanks! Your review has been added.")
        return redirect("shop:product_detail", pk=product.pk)

    # Re-render the detail page with the bound (invalid) form so errors show.
    view = ProductDetailView()
    view.setup(request, pk=pk)
    view.object = product
    context = view.get_context_data(object=product, review_form=form)
    messages.error(request, "Please correct the errors in your review.")
    return render(request, view.template_name, context)


def landing(request):
    """Public landing page showcasing featured products and categories."""
    products = Product.objects.none()

    if request.user.is_authenticated:
        products = request.user.recommendations.all()

    categories = Category.objects.all()[:8]
    return render(
        request,
        "shop/landing.html",
        {
            "products": products,
            "categories": categories,
        },
    )


@csrf_exempt
@require_http_methods(["POST"])
def recommendations_webhook(request):
    data = json.loads(request.body)

    import boto3
    import os

    s3 = boto3.client("s3")

    print(json.dumps(data, indent=4))

    records = data.get("Records")

    if not records:
        return JsonResponse({"error": "No records provided"}, status=400)

    object_data = records[0].get("s3", {}).get("object")

    if not object_data:
        return JsonResponse({"error": "No object data provided"}, status=400)

    key = object_data.get("key")

    filename = key.split("/")[-1]

    file_path = f"/tmp/{filename}"

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    s3.download_file(bucket_name, key, file_path)

    # Group by user id to improve insertion into the database
    group_by_user_id = dict()

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("userId") not in group_by_user_id:
                group_by_user_id[row.get("userId")] = [
                    row.get("productId")
                ]
            else:
                group_by_user_id[row.get("userId")].append(
                    row.get("productId")
                )

    with transaction.atomic():
        for user_id, product_ids in group_by_user_id.items():
            products = Product.objects.filter(id__in=product_ids)
            user = User.objects.get(id=user_id)
            user.recommendations.set(products)

    print("Successfully loaded recommendations")

    return JsonResponse({"message": "Success"}, status=200)
