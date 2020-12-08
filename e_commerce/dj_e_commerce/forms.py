from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)

class CheckOutForm(forms.Form):

    street_address = forms.CharField(
                                     widget=forms.TextInput(attrs={'placeholder': '1234  Str '}))
    apartment_address = forms.CharField(required=False,
                                        widget=forms.TextInput(attrs={'placeholder': 'Apartment or suite '})
                                        )
    country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))


    zip = forms.CharField(required=False,
                                     widget=forms.TextInput(attrs={'placeholder': ''}))
    same_shipping_address = forms.BooleanField (required=False, widget= forms.CheckboxInput())
    save_info = forms.BooleanField (required=False, widget= forms.CheckboxInput())
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)