from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('signup'),
            '/admin/login/',
            '/admin/',
        ]
        
        # Check if user is not authenticated and trying to access protected URL
        if not request.user.is_authenticated and request.path not in public_urls:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        # If user is authenticated and trying to access login page, redirect to dashboard
        if request.user.is_authenticated and request.path == reverse('login'):
            return redirect('index')
        
        response = self.get_response(request)
        
        # Add cache control headers
        if not request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response 