from django.db import models

class Produit(models.Model): 
    nom = models.CharField(max_length=200, unique=True) 
    quantite = models.IntegerField(default=0) 
    prix = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return self.nom 