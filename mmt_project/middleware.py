from django.shortcuts import redirect

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_urls = ['/login/', '/register/', '/admin/', '/static/', '/media/']

        if not request.user.is_authenticated:
            is_exempt = any(request.path.startswith(url) for url in exempt_urls)
            if not is_exempt:
                return redirect('/login/?next=' + request.path)
        
        response = self.get_response(request)
        return response
