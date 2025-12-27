from django.contrib import admin
from .models import BMIResult

@admin.register(BMIResult)
class BMIResultAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'bmi',
        'kategori',
        'penyakit_terdeteksi',
        'created_at'
    )
    list_filter = ('kategori', 'penyakit_terdeteksi')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
