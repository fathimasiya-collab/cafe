from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .models import FoodItem, Category
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import CartItem,Order


def home(request):
    categories = Category.objects.all()
    food_items = FoodItem.objects.all()

    return render(request, 'menu/home.html', {
        'categories': categories,
        'food_items': food_items,
    })


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'menu/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'menu/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')

def menu_page(request):
    categories = Category.objects.all()
    food_items = FoodItem.objects.all()

    return render(request, 'menu/menu.html', {
        'categories': categories,
        'food_items': food_items,
    })
@login_required
def add_to_cart(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id)

    cart_item, created = CartItem.objects.get_or_create(
        customer=request.user,
        food_item=food
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{food.name} added to your cart!")

    return redirect('menu')


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(customer=request.user)

    total = sum(
        item.food_item.price * item.quantity
        for item in cart_items
    )

    return render(request, 'menu/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def checkout(request):

    cart_items = list(
        CartItem.objects.filter(customer=request.user)
    )

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    total = sum(
        item.food_item.price * item.quantity
        for item in cart_items
    )

    if request.method == 'POST':

        customer_name = request.POST.get('customer_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()

        if not customer_name or not phone or not delivery_address:
            messages.error(request, "Please fill in all the details.")

        else:
            from django.db import transaction

            with transaction.atomic():

                for item in cart_items:
                    Order.objects.create(
                        customer=request.user,
                        food_item=item.food_item,
                        quantity=item.quantity,
                        customer_name=customer_name,
                        phone=phone,
                        delivery_address=delivery_address
                    )

                CartItem.objects.filter(
                    customer=request.user
                ).delete()

            messages.success(request, "Your order has been placed successfully!")
            return redirect('order_success')

    return render(request, 'menu/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })


@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            customer=request.user
        )
        cart_item.delete()

    return redirect('cart')

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            customer=request.user
        )

        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('cart')
@login_required
def order_success(request):
    return render(request, 'menu/order_success.html')