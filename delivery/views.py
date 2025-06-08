from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Customer, Restaurant, Item, Cart

import razorpay
from django.conf import settings

# Create your views here.
def index(request):
    return render(request, 'delivery/index.html')

def open_signin(request):
    return render(request, 'delivery/signin.html')

def open_signup(request):
    return render(request, 'delivery/signup.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        if Customer.objects.filter(username=username).exists():
            return HttpResponse("Duplicate username!")
        else:
            Customer.objects.create(
                username=username,
                password=password,
                email=email,
                mobile=mobile,
                address=address,
            )
            return render(request, 'delivery/signin.html')

    return render(request, 'delivery/signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        customer = Customer.objects.filter(username=username, password=password).first()

        if customer:
            if username == 'admin':
                return render(request, 'delivery/admin_home.html')
            else:
                restaurantList = Restaurant.objects.all()
                return render(request, 'delivery/customer_home.html', {
                    "restaurantList": restaurantList,
                    "username": username
                })
        else:
            return render(request, 'delivery/fail.html')

    return render(request, 'delivery/signin.html')

def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        if Restaurant.objects.filter(name=name).exists():
            return HttpResponse("Duplicate restaurant!")
        else:
            Restaurant.objects.create(
                name=name,
                picture=picture,
                cuisine=cuisine,
                rating=rating,
            )
    return render(request, 'delivery/admin_home.html')

def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})

def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    return render(request, 'delivery/update_restaurant.html', {"restaurant": restaurant})

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    if request.method == 'POST':
        restaurant.name = request.POST.get('name')
        restaurant.picture = request.POST.get('picture')
        restaurant.cuisine = request.POST.get('cuisine')
        restaurant.rating = request.POST.get('rating')
        restaurant.save()

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})

def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    restaurant.delete()

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})

def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'delivery/update_menu.html', {"itemList": itemList, "restaurant": restaurant})

def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')

        if Item.objects.filter(name=name).exists():
            return HttpResponse("Duplicate item!")
        else:
            Item.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                vegeterian=vegeterian,
                picture=picture,
            )
    return render(request, 'delivery/admin_home.html')

def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'delivery/customer_menu.html', {
        "itemList": itemList,
        "restaurant": restaurant,
        "username": username
    })

def add_to_cart(request, item_id, username):
    item = Item.objects.get(id=item_id)
    customer = Customer.objects.filter(username=username).first()

    if not customer:
        return HttpResponse("Customer not found.")

    cart, created = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)

    return HttpResponse('added to cart')

def show_cart(request, username):
    customer = Customer.objects.filter(username=username).first()
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    return render(request, 'delivery/cart.html', {
        "itemList": items,
        "total_price": total_price,
        "username": username
    })

def checkout(request, username):
    customer = Customer.objects.filter(username=username).first()
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(request, 'delivery/checkout.html', {
            'error': 'Your cart is empty!',
        })

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order_data = {
        'amount': int(total_price * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',
    }
    order = client.order.create(data=order_data)

    return render(request, 'delivery/checkout.html', {
        'username': username,
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],
        'amount': total_price,
    })

def orders(request, username):
    customer = Customer.objects.filter(username=username).first()
    cart = Cart.objects.filter(customer=customer).first()

    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if cart:
        cart.items.clear()

    return render(request, 'delivery/orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })
