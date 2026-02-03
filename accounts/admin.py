from django.contrib import admin
from .models import BMIResult, WeeklyMealPlan, MentalHealthLog
from django.utils.html import format_html

@admin.register(BMIResult)
class BMIResultAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'bmi',
        'kategori_badge',
        'penyakit_terdeteksi',
        'created_at'
    )

    list_filter = ('kategori', 'penyakit_terdeteksi')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)

    def kategori_badge(self, obj):
        warna = {
            "Kurus": "#0d6efd",            
            "Normal (Ideal)": "#198754",   
            "Overweight": "#fd7e14",       
            "Obesitas": "#dc3545",        
        }.get(obj.kategori, "#6c757d")

        return format_html(
            '<span style="'
            'background:{};'
            'color:white;'
            'padding:4px 10px;'
            'border-radius:12px;'
            'font-weight:600;'
            'font-size:12px;">'
            '{}</span>',
            warna,
            obj.kategori
        )

    kategori_badge.short_description = "Kategori BMI"

@admin.register(WeeklyMealPlan)
class WeeklyMealPlanAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'week',
        'year',
        'created_at',
        'meal_plan',
    )
    list_filter = ('week', 'year')
    search_fields = ('user__username', 'meal_plan')
    ordering = ('-year', '-week')

@admin.register(MentalHealthLog)
class MentalHealthLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'kondisi', 'created_at')
    ordering = ('-created_at',)