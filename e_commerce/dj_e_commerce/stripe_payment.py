import stripe
def stripe_payment (secret_key, token, amount, description ):
    try:
        print(secret_key, token, amount, description, )
        # Use Stripe's library to make requests...
        stripe.api_key = secret_key
        # Token is created using Stripe Checkout or Elements!
        # Get the payment token ID submitted by the form:
        charge = stripe.Charge.create(
            amount= int (amount * 100),
            currency='usd',
            description=description,
            source=token,
        )
        return charge['id']
    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught

        print('Status is: %s' % e.http_status)
        print('Code is: %s' % e.code)
        # param is '' in this case
        print('Param is: %s' % e.param)
        print('Message is: %s' % e.user_message)
    except stripe.error.RateLimitError as e:
        print (e)
    except stripe.error.InvalidRequestError as e:
        print (e)

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        print (e)

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        print (e)

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        print (e)

    except Exception as e:
        # Something else happened, completely unrelated to Stripe
        print (e)

    return None