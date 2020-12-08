from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django_countries.fields import CountryField

User = get_user_model()

CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('SW', 'Sport wear'),
    ('OW', 'Outwear')
)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

class Item(models.Model):
    title = models.CharField(max_length= 100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null= True)
    description = models.CharField (max_length= 1000, blank= True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length= 10, default='S')
    label = models.CharField(choices=LABEL_CHOICES, max_length= 10, default='P')
    slug = models.SlugField(unique= True)
    image = models.ImageField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse ('dj_e_commerce:product', kwargs = {'slug': self.slug})

    def get_add_to_cart_url(self):
        return reverse ('dj_e_commerce:add-to-cart', kwargs = {'slug': self.slug})

    def get_price(self):
        if (self.discount_price):
            return self.discount_price
        return self.price



class OrderItem(models.Model):
    item = models.ForeignKey (Item , on_delete= models.CASCADE)
    quantity = models.IntegerField (default= 1)


    def __str__(self):
        return str(self.item.title) + str(self.quantity)

    def get_total_price (self):
        if (self.item.discount_price):
            return self.quantity * self.item.discount_price
        return self.quantity * self.item.price

    def get_amount_saved(self):
        if (self.item.discount_price):
            return self.quantity*self.item.price - self.quantity * self.item.discount_price
        return 0



class Order(models.Model):
    user = models.ForeignKey (User, on_delete= models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date  = models.DateTimeField()
    ordered = models.BooleanField(default= False)
    billing_address = models.ForeignKey('BillingAddress', on_delete=  models.SET_NULL, blank= True,
                                        null= True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True,
                                        null=True)

    def __str__(self):
        return self.user.username

    def get_total (self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_price()
        return total

class BillingAddress(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    #address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    #default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    stripe_charge_id = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username

class Coupon(models.Model) :
    code = models.CharField(max_length = 15)

    def __str__(self):
        return self.code