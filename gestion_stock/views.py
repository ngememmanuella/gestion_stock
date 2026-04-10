from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


# Create your views here.

def admin_view(request):
    return render(request, 'gestion/admin.html')

def gestionaire_view(request):
    return render(request, 'gestion/gestionaire.html')

def secretaire_view(request):
    return render(request, 'gestion/secretaire.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  # redirige vers une page définie dans urls.py
        else:
            messages.error(request, "Identifiants incorrects")

    return render(request, 'login.html')