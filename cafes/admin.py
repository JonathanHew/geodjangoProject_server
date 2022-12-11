from django.contrib import admin

# Register your models here.
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Cafe

@admin.register(Cafe)
class ShopAdmin(OSMGeoAdmin):
    list_display = ('name', 'location')