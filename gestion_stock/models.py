from django.db import models
from django.contrib.auth.models import User

class Produit(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    quantite = models.IntegerField(default=0)
    prix = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nom

class Mouvement(models.Model):
    TYPES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=10, choices=TYPES)
    quantite = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type_mouvement} - {self.produit.nom} ({self.quantite})"