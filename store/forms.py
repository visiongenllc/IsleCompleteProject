from django import forms
from .models import Dino, CoinPackage

class DinosaurForm(forms.ModelForm):
    class Meta:
        model = Dino
        fields = ['name', 'coin_cost', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'coin_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class CoinPackageForm(forms.ModelForm):
    class Meta:
        model = CoinPackage
        fields = ['name', 'coins_amount', 'price_usd']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'coins_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_usd': forms.NumberInput(attrs={'class': 'form-control'}),
        }
