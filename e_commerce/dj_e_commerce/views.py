from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from .forms import CheckOutForm
from .models import *
from.stripe_payment import *
import stripe

# Create your views here.


class HomeView(ListView):
    """
    Home View
    """
    model = Item
    # 10 page pagination
    paginate_by = 10
    template_name = 'home-page.html'


class OrderSummaryView(LoginRequiredMixin, View):
    '''
    Renders order-summary page
    '''
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            return render(self.request, 'order-summary.html', {'object': order})
        except ObjectDoesNotExist:
            return redirect('/')




class ItemDetailView( DetailView):
    '''
    Renders detail view for a single item
    '''
    model = Item
    template_name = 'product-page.html'

@login_required
def add_to_cart(request, slug):
    '''
    Is triggered when 'Add to cart' button is pushed
    :param request: POST request from form
    :param slug: unique slug of item
    :return: rendering of new page
    '''
    # Get the Item and the Order, which includes that Item
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # Find the OrderItem and update the quantity
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            quant = order_item[0].quantity
            order_item.update(quantity=quant + int(request.POST.get('quantity')))
            messages.info(request, "This item has been added to your cart")

        else:
            #Create a new product Order Item and append it to the Order
            order_item = OrderItem.objects.create(item=item)
            order.items.add(order_item)
            messages.info(request, "This item has been added to your cart")

    else:
        #Create new order
        ordered_date = timezone.now()
        order_item = OrderItem.objects.create(item=item)
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item has been added to your cart")
    return redirect('dj_e_commerce:product', slug=slug)

@login_required
def remove_from_cart(request, slug):
    '''
    :param request: POST request
    :param slug: Unique slug of the iten
    :return: Rendered page
    '''
    #Get the Item and its Order
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        # Delete item from the cart
        if order_item.exists():
            order.items.remove(order_item[0])
            messages.info(request, "Item successfully removed from your cart")
        else:
            messages.info(request, "No such item in your cart")
    else:
        messages.info(request, "No such item in your cart")

    return redirect('dj_e_commerce:product', slug=slug)

@login_required
def decrease_quantity(request, slug):
    '''
    Decrease slug-item from the cart by one unit.
    :param request: POST request
    :param slug: Unique slug of the iten
    :return: Rendered page
    '''
    #Get the Item and its Order
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            quant = order_item[0].quantity
            if (quant > 1):
                #Decrease amount by one unit
                order_item.update(quantity=quant - 1)
        else:
            messages.info(request, "No such item in your cart")

    else:
        messages.info(request, "No such item in your cart")

    return redirect('dj_e_commerce:order-summary')

@login_required
def increase_quantity(request, slug):
    '''
    Increase slug-item from the cart by one unit.
    :param request: POST request
    :param slug: Unique slug of the iten
    :return: Rendered page
    '''

    #Get the Item and its Order
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            quant = order_item[0].quantity
            # Increase quanity by one unit
            order_item.update(quantity=quant + 1)
        else:
            messages.info(request, "No such item in your cart")

    else:
        messages.info(request, "No such item in your cart")

    return redirect('dj_e_commerce:order-summary')






class PaymentView (LoginRequiredMixin, View):
    '''
    Handle Stripe payment (Stripe API)
    '''
    def get (self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            'order': order
        }
        return render (self.request, 'payment.html', context)

    def post(self,*args, **kwargs):
        # Create Stripe payment
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        chargeID = stripe_payment(settings.STRIPE_SECRET_KEY,token, order.get_total(),str(order.id))
        if (chargeID is not None):
            order.ordered = True

            # Save the payment
            payment = Payment()
            payment.stripe_charge_id = chargeID
            payment.user = self.request.user
            payment.price = order.get_total() * 100
            payment.save()
            order.payment = payment
            order.save()
            return redirect('/')
        else:
            messages.error(self.request, "Something went wrong with Stripe. Please try again later")
            return redirect ('dj_e_commerce:payment', payment_option= 'S')



class CheckOutView( LoginRequiredMixin,  View):
    '''
    Checkout page
    1. Save shipping address and related information
    '''
    def get(self, *args, **kwargs):
        form = CheckOutForm()
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'form': form, 'order':order}
            return render(self.request, 'checkout-page.html', context)
        except ObjectDoesNotExist:
            return redirect('/')


    def post(self, *args, **kwargs):
        form = CheckOutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user= self.request.user, ordered = False)

            if form.is_valid():
                # Get the shipping information and save them into the database.
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                same_shipping_address = form.cleaned_data.get('same_shipping_address')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billingAddress = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                )
                billingAddress.save()
                # Connect address with order (Foreign Key)
                order.billing_address = billingAddress
                order.save()
                return redirect('dj_e_commerce:payment', payment_option= payment_option)
            return render(self.request, 'checkout-page.html', {'form':form})

        except ObjectDoesNotExist:
            messages.warning(self.request, "You don't have any active order")
            return redirect('dj_e_commerce:order-summary')


def signup(request):
    '''
    Sign up page. We use the default django's User Creation Form.
    :param request: POST request
    :return: Sign up page
    '''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Get username, passwords and save them into the database
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('login')
    else:
        # Create UserCreationForm
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})



