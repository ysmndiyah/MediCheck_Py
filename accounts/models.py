from django.db import models
from django.contrib.auth.models import User


class BMIResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    berat = models.FloatField()
    tinggi = models.FloatField()
    bmi = models.FloatField()
    kategori = models.CharField(max_length=50)
    riwayat_input = models.TextField()
    penyakit_terdeteksi = models.TextField()
    rekomendasi = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - BMI {self.bmi}"


class HealthTarget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    berat_sekarang = models.FloatField()
    berat_ideal = models.FloatField()

    kalori_harian = models.IntegerField()
    kalori_target = models.IntegerField()

    progress_berat = models.IntegerField()
    progress_kalori = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Target {self.user.username}"

class HealthLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    berat = models.FloatField()
    tinggi = models.FloatField()
    bmi = models.FloatField()
    kalori = models.IntegerField()
    tanggal = models.DateField(auto_now_add=True)

    def minggu(self):
        return self.tanggal.isocalendar()[1]
    
class WeeklyMealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    kondisi_kesehatan = models.TextField()
    alergi_makanan = models.TextField()

    week = models.IntegerField()
    year = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'week', 'year')

    def __str__(self):
        return f"{self.user.username} - Week {self.week} {self.year}"
    
class MentalHealthLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    kondisi = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.kondisi} ({self.created_at.date()})"

