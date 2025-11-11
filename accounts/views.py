from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


# ===================== LOGIN DENGAN EMAIL =====================
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Cari user berdasarkan email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username  # gunakan username internal
        except User.DoesNotExist:
            messages.error(request, "Email tidak ditemukan.")
            return render(request, 'accounts/login.html')

        # Autentikasi
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Selamat datang, {user.first_name or user.username}!")
            return redirect('accounts:bmi')  # ganti nanti ke halaman beranda BMI
        else:
            messages.error(request, "Password salah.")
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')


# ===================== REGISTER DENGAN EMAIL & NAMA LENGKAP =====================
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        # Validasi input
        if not email or not full_name or not password or not password2:
            messages.error(request, "Semua field harus diisi.")
            return render(request, 'accounts/register.html')

        if password != password2:
            messages.error(request, "Password dan konfirmasi password tidak cocok.")
            return render(request, 'accounts/register.html')

        if len(password) < 6:
            messages.error(request, "Password minimal 6 karakter.")
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email sudah terdaftar.")
            return render(request, 'accounts/register.html')

        # Buat akun user baru
        try:
            username = email  # gunakan email sebagai username
            user = User.objects.create_user(username=username, email=email, password=password)

            # Simpan nama lengkap (split ke first_name dan last_name)
            names = full_name.split()
            if len(names) == 1:
                user.first_name = names[0]
            else:
                user.first_name = names[0]
                user.last_name = " ".join(names[1:])
            user.save()

            messages.success(request, "Akun berhasil dibuat! Silakan login.")
            return redirect('accounts:login')

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {e}")
            return render(request, 'accounts/register.html')

    return render(request, 'accounts/register.html')


def bmi_view(request):
    bmi = None
    kategori = None
    rekomendasi = []

    if request.method == 'POST':
        try:
            berat = float(request.POST.get('berat'))
            tinggi = float(request.POST.get('tinggi')) / 100  # ubah cm ke meter
            bmi = berat / (tinggi ** 2)

            if bmi < 18.5:
                kategori = "Kurus"
                rekomendasi = [
                    "Makan lebih sering dengan porsi kecil.",
                    "Tambahkan makanan tinggi protein (telur, ayam, ikan).",
                    "Perbanyak asupan karbohidrat kompleks (nasi merah, kentang)."
                ]
            elif 18.5 <= bmi < 25:
                kategori = "Normal (Ideal)"
                rekomendasi = [
                    "Pertahankan pola makan seimbang.",
                    "Rutin olahraga minimal 3x seminggu.",
                    "Tidur cukup dan jaga hidrasi tubuh."
                ]
            elif 25 <= bmi < 30:
                kategori = "Overweight"
                rekomendasi = [
                    "Kurangi konsumsi gula dan gorengan.",
                    "Perbanyak buah, sayur, dan air putih.",
                    "Lakukan aktivitas fisik secara rutin."
                ]
            else:
                kategori = "Obesitas"
                rekomendasi = [
                    "Konsultasi dengan ahli gizi atau dokter.",
                    "Kurangi makanan tinggi lemak jenuh.",
                    "Olahraga ringan setiap hari."
                ]
        except (ValueError, ZeroDivisionError):
            messages.error(request, "Input tidak valid. Pastikan angka dimasukkan dengan benar.")

    return render(request, 'accounts/bmi.html', {
        'bmi': bmi,
        'kategori': kategori,
        'rekomendasi': rekomendasi
    })

from django.contrib.auth.decorators import login_required

@login_required(login_url='accounts:login')
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


