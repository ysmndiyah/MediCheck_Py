from django.contrib import admin
from .models import BMIResult, WeeklyMealPlan, MentalHealthLog

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

@admin.register(WeeklyMealPlan)
class WeeklyMealPlanAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'kondisi_kesehatan',
        'alergi_makanan',
        'week',
        'year',
        'created_at'
    )
    list_filter = ('week', 'year')
    search_fields = ('user__username', 'kondisi_kesehatan')
    ordering = ('-year', '-week')

@admin.register(MentalHealthLog)
class MentalHealthLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'kondisi', 'created_at')
    ordering = ('-created_at',)