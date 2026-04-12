from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Produit, Mouvement


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
    return render(request, 'gestion_stock/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def home_view(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    groups = request.user.groups.values_list('name', flat=True)
    if 'gestionnaire' in groups:
        return redirect('gestionnaire')
    elif 'secretaire' in groups:
        return redirect('secretaire')
    return redirect('admin_dashboard')


@login_required(login_url='/login/')
def admin_dashboard(request):
    produits = Produit.objects.all()
    total_produits = produits.count()
    valeur_stock = sum(p.prix * p.quantite for p in produits)
    alertes = produits.filter(quantite__lt=10).count()
    derniers_mouvements = Mouvement.objects.select_related('produit', 'utilisateur').order_by('-date')[:10]
    for p in produits:
        p.valeur_totale = p.prix * p.quantite
    return render(request, 'gestion_stock/admin_dashboard.html', {
        'produits': produits,
        'total_produits': total_produits,
        'valeur_stock': valeur_stock,
        'alertes': alertes,
        'derniers_mouvements': derniers_mouvements,
    })


@login_required(login_url='/login/')
def gestionnaire_view(request):
    produits = Produit.objects.all().order_by('nom')
    return render(request, 'gestion_stock/gestionnaire.html', {'produits': produits})


@login_required(login_url='/login/')
def ajouter_produit(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        quantite = int(request.POST.get('quantite', 0))
        prix = request.POST.get('prix', 0)
        if nom:
            produit = Produit.objects.create(nom=nom, quantite=quantite, prix=prix)
            if quantite > 0:
                Mouvement.objects.create(
                    produit=produit,
                    type_mouvement='entree',
                    quantite=quantite,
                    utilisateur=request.user,
                    note='Stock initial à la création'
                )
            messages.success(request, f'Produit "{nom}" ajouté avec succès.')
        else:
            messages.error(request, 'Le nom du produit est requis.')
    return redirect('gestionnaire')


@login_required(login_url='/login/')
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        ancienne_qte = produit.quantite
        produit.nom = request.POST.get('nom', produit.nom).strip()
        nouvelle_qte = int(request.POST.get('quantite', produit.quantite))
        produit.prix = request.POST.get('prix', produit.prix)
        produit.quantite = nouvelle_qte
        produit.save()
        # Enregistrer le mouvement si la quantité a changé
        diff = nouvelle_qte - ancienne_qte
        if diff > 0:
            Mouvement.objects.create(
                produit=produit,
                type_mouvement='entree',
                quantite=diff,
                utilisateur=request.user,
                note='Ajustement de stock'
            )
        elif diff < 0:
            Mouvement.objects.create(
                produit=produit,
                type_mouvement='sortie',
                quantite=abs(diff),
                utilisateur=request.user,
                note='Ajustement de stock'
            )
        messages.success(request, f'Produit "{produit.nom}" mis à jour.')
    return redirect('gestionnaire')


@login_required(login_url='/login/')
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f'Produit "{nom}" supprimé.')
    return redirect('gestionnaire')


@login_required(login_url='/login/')
def mouvement_view(request):
    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        type_mvt = request.POST.get('type_mouvement')
        quantite = int(request.POST.get('quantite', 0))
        note = request.POST.get('note', '')
        produit = get_object_or_404(Produit, pk=produit_id)
        if type_mvt == 'sortie' and quantite > produit.quantite:
            messages.error(request, f'Stock insuffisant. Disponible : {produit.quantite}')
        elif quantite <= 0:
            messages.error(request, 'La quantité doit être supérieure à 0.')
        else:
            if type_mvt == 'entree':
                produit.quantite += quantite
            else:
                produit.quantite -= quantite
            produit.save()
            Mouvement.objects.create(
                produit=produit,
                type_mouvement=type_mvt,
                quantite=quantite,
                utilisateur=request.user,
                note=note
            )
            messages.success(request, f'Mouvement enregistré pour "{produit.nom}".')
        return redirect('mouvements')

    produits = Produit.objects.all().order_by('nom')
    mouvements = Mouvement.objects.select_related('produit', 'utilisateur').order_by('-date')
    return render(request, 'gestion_stock/mouvements.html', {
        'produits': produits,
        'mouvements': mouvements,
    })


@login_required(login_url='/login/')
def secretaire_view(request):
    produits = Produit.objects.all().order_by('nom')
    mouvements = Mouvement.objects.select_related('produit', 'utilisateur').order_by('-date')[:20]
    return render(request, 'gestion_stock/secretaire.html', {
        'produits': produits,
        'mouvements': mouvements,
    })


# ─── Étape 2 : Gestion des utilisateurs ───────────────────────────────────────
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
def utilisateurs_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé à l'administrateur.")
        return redirect('home')
    utilisateurs = User.objects.exclude(is_superuser=True).select_related().prefetch_related('groups')
    groupes = Group.objects.all()
    return render(request, 'gestion_stock/utilisateurs.html', {
        'utilisateurs': utilisateurs,
        'groupes': groupes,
    })


@login_required(login_url='/login/')
def creer_utilisateur(request):
    if not request.user.is_superuser:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        groupe_id = request.POST.get('groupe')
        if not username or not password:
            messages.error(request, 'Nom d\'utilisateur et mot de passe requis.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'L\'utilisateur "{username}" existe déjà.')
        else:
            user = User.objects.create_user(username=username, password=password)
            if groupe_id:
                try:
                    groupe = Group.objects.get(pk=groupe_id)
                    user.groups.add(groupe)
                except Group.DoesNotExist:
                    pass
            messages.success(request, f'Utilisateur "{username}" créé avec succès.')
    return redirect('utilisateurs')


@login_required(login_url='/login/')
def toggle_utilisateur(request, pk):
    if not request.user.is_superuser:
        return redirect('home')
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        etat = 'activé' if user.is_active else 'désactivé'
        messages.success(request, f'Compte "{user.username}" {etat}.')
    return redirect('utilisateurs')


@login_required(login_url='/login/')
def supprimer_utilisateur(request, pk):
    if not request.user.is_superuser:
        return redirect('home')
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        nom = user.username
        user.delete()
        messages.success(request, f'Utilisateur "{nom}" supprimé.')
    return redirect('utilisateurs')
