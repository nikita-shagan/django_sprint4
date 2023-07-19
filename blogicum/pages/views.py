from django.shortcuts import render


def page_not_found(request, exception):
    """Handle error 404."""
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    """Handle error 403."""
    return render(request, 'pages/403csrf.html', status=403)


def internal_server_error(request):
    """Handle error 500."""
    return render(request, 'pages/500.html', status=500)
