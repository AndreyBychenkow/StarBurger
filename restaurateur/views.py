from django import forms
from django.shortcuts import redirect, render

from django.views import View
from django.urls import reverse_lazy

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login

from django.contrib.auth import views as auth_views
from django.http import JsonResponse

from foodcartapp.models import Product, Restaurant, Order, \
    OrderItem

from django.db.models import Sum, F
from django.db import transaction


class Login(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control",
                   "placeholder": "Укажите имя пользователя"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={"form": form})

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(
            request,
            "login.html",
            context={
                "form": form,
                "ivalid": True,
            },
        )


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("restaurateur:login")


def is_manager(user):
    return user.is_staff


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_products(request):
    restaurants = list(Restaurant.objects.order_by("name"))
    products = list(Product.objects.prefetch_related("menu_items"))

    products_with_restaurant_availability = []
    for product in products:
        availability = {
            item.restaurant_id: item.availability for item in
            product.menu_items.all()
        }
        ordered_availability = [
            availability.get(restaurant.id, False) for restaurant in restaurants
        ]

        products_with_restaurant_availability.append((product, ordered_availability))

    return render(
        request,
        "products_list.html",
        {
            "products_with_restaurant_availability": products_with_restaurant_availability,
            "restaurants": restaurants,
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_restaurants(request):
    return render(
        request,
        template_name="restaurants_list.html",
        context={
            "restaurants": Restaurant.objects.all(),
        },
    )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(status='completed').annotate(
        custom_total_price=Sum(F('items__quantity') * F('items__product__price'))
    ).prefetch_related('items__product').all()
    return render(request, 'manager_orders.html', {'orders': orders})


def create_order_view(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        phonenumber = request.POST.get('phonenumber')
        address = request.POST.get('address')

        items = [
            {'product': Product.objects.get(id=1), 'quantity': 2},
            {'product': Product.objects.get(id=2), 'quantity': 1}
        ]

        try:
            with transaction.atomic():
                order = Order(
                    firstname=firstname,
                    lastname=lastname,
                    phonenumber=phonenumber,
                    address=address
                )
                order.save()

                total_price = 0

                for item in items:
                    product = item['product']
                    quantity = item['quantity']

                    order_item = OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    order_item.save()
                    total_price += product.price * quantity

                order.total_price = total_price
                order.save()

            return JsonResponse(
                {'order_id': order.id, 'total_price': order.total_price})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
