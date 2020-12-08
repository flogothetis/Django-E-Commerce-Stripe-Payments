from django.urls import path
from .views import  *

app_name = 'dj_e_commerce'
urlpatterns = [
    path('', HomeView.as_view(), name = 'home'),
    path('product/<slug>/', ItemDetailView.as_view(), name = 'product'),
    path('checkout/',CheckOutView.as_view(), name = 'checkout'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('signup/', signup, name='signup'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('increase-quantity/<slug>/', increase_quantity, name='increase-quantity'),
    path('decrease-quantity/<slug>/', decrease_quantity, name='decrease-quantity'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),

]