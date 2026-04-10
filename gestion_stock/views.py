from django.shortcuts import render

# Create your views here.

def admin_view(request):
    return render(request, 'gestion/admin.html')

def gestionaire_view(request):
    return render(request, 'gestion/gestionaire.html')

def secretaire_view(request):
    return render(request, 'gestion/secretaire.html')