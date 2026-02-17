from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category

# Product List
from django.db.models import Q

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    search_query = request.GET.get('search')

    if category_id:
        products = products.filter(category_id=category_id)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    context = {
        'products': products,
        'categories': categories
    }

    return render(request, 'product_list.html', context)


# Add to Cart (Session Based)
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1

    request.session['cart'] = cart
    return redirect('product_list')


# View Cart
def view_cart(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        subtotal = product.price * quantity
        total += subtotal

        products.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'cart.html', {
        'products': products,
        'total': total
    })
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('view_cart')
def update_cart(request, product_id, action):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        if action == "increase":
            cart[str(product_id)] += 1
        elif action == "decrease":
            cart[str(product_id)] -= 1

            if cart[str(product_id)] <= 0:
                del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('view_cart')
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required

@login_required
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('product_list')

    order = Order.objects.create(
        user=request.user,
        total_price=0
    )

    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        subtotal = product.price * quantity
        total += subtotal

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        # Reduce stock
        product.stock -= quantity
        product.save()

    order.total_price = total
    order.save()

    # Clear cart
    request.session['cart'] = {}

    return render(request, 'order_success.html', {'order': order})
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})
