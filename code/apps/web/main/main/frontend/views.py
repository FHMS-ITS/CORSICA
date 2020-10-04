from django.shortcuts import render


def about(request):
    return_data = {}
    return render(request, 'frontend/about.html', return_data)
