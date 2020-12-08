from django import template

from dj_e_commerce.models import Order

register = template.Library()

@register.filter
def cart_item_count(user):
    if (user.is_authenticated):
        qs = Order.objects.filter(user = user , ordered = False)
        if qs.exists():
            return qs[0].items.count()
    return 0
