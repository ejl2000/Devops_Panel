from django.http import JsonResponse
from django.utils import timezone
from devopspanel.core.models import BearerToken

def bearer_token_required(view_func):
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Bearer token required'}, status=401)
        token = auth_header[7:]  # Remove prefix 'Bearer '
        try:
            bearer_token = BearerToken.objects.get(token=token)
            if bearer_token.is_expired():
                return JsonResponse({'error': 'Token expired'}, status=401)
            request.user = bearer_token.user  # Set User in request
            return view_func(request, *args, **kwargs)
        except BearerToken.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=401)
    return wrapped_view
