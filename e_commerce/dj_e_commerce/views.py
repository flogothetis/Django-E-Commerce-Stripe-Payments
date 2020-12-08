from django.conf import settings
from django.contrib import messages
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
    model = Item
    paginate_by = 10
    template_name = 'home-page.html'


class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            return render(self.request, 'order-summary.html', {'object': order})
        except ObjectDoesNotExist:
            return redirect('/')


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product-page.html'


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            quant = order_item[0].quantity
            order_item.update(quantity=quant + int(request.POST.get('quantity')))
            messages.info(request, "This item was added to the cart")

        else:
            order_item = OrderItem.objects.create(item=item)
            order.items.add(order_item)
            messages.info(request, "This item was added to the cart")

    else:
        ordered_date = timezone.now()
        order_item = OrderItem.objects.create(item=item)
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to the cart")

    return redirect('dj_e_commerce:product', slug=slug)


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            order.items.remove(order_item[0])
            messages.info(request, "Item successfully removed from the cart")
        else:
            messages.info(request, "No such item in your cart")

    else:
        messages.info(request, "No such item in your cart")

    return redirect('dj_e_commerce:product', slug=slug)


def decrease_quantity(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            quant = order_item[0].quantity
            if (quant > 1):
                order_item.update(quantity=quant - 1)
        else:
            messages.info(request, "No such item in your cart")

    else:
        messages.info(request, "No such item in your cart")

    return redirect('dj_e_commerce:order-summary')


def increase_quantity(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item = order.items.filter(item__slug=slug)
        if order_item.exists():
            quant = order_item[0].quantity
            order_item.update(quantity=quant + 1)
        else:
            messages.info(request, "No such item in your cart")

    else:
        messages.info(request, "No such item in your cart")

    return redirect('dj_e_commerce:order-summary')





class PaymentView (View):
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

            # create a payment
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



class CheckOutView(View):
    def get(self, *args, **kwargs):

        form = CheckOutForm()
        context = {'form': form}
        return render(self.request, 'checkout-page.html', context)

    def post(self, *args, **kwargs):
        form = CheckOutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user= self.request.user, ordered = False)

            if form.is_valid():
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
                #connect address with order
                order.billing_address = billingAddress
                order.save()
                return redirect('dj_e_commerce:payment', payment_option= payment_option)
            return render(self.request, 'checkout-page.html', {'form':form})

        except ObjectDoesNotExist:
            messages.warning(self.request, "You don't have any active order")
            return redirect('dj_e_commerce:order-summary')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})
