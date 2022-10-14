from datetime import datetime
from functools import wraps
from graphql_jwt import Verify


def access_required(function):
    """
    Check if the user is logged on the system.
    """
    @wraps(function)
    def decorated(*args, **kwargs):
        token = args[1].context.META.get('HTTP_AUTHORIZATION')
        if not token:
            raise Exception('Unauthorized')
        try:
            _, token = token.split('Bearer ')
        except:
            raise Exception('Invalid authorization method')

        validator = Verify.Field()
        try:
            payload = validator.resolver(None, args[1], token).payload
        except:
            raise Exception('Unauthorized')

        token_exp = datetime.fromtimestamp(payload['exp'])
        now = datetime.now()
        if token_exp < now:
            raise Exception('Session expired')

        token_user = payload['username']
        input_user = kwargs['username']
        if token_user != input_user:
            raise Exception('Invalid credentials for this user')

        return function(*args, **kwargs)
    return decorated