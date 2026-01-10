from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import BMIResult
from django.contrib.auth import logout
from django.http import JsonResponse
from .models import HealthLog
from django.utils import timezone
from datetime import timedelta
from .models import WeeklyMealPlan
from datetime import date
from .models import MentalHealthLog
from django.contrib.admin.views.decorators import staff_member_required



# ===================== LOGIN DENGAN EMAIL =====================
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # ================= CARI USER BERDASARKAN EMAIL =================
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Email tidak ditemukan.")
            return render(request, 'accounts/login.html')

        # ================= AUTENTIKASI =================
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            messages.success(
                request,
                f"Selamat datang, {user.first_name or user.username}!"
            )

            # ================= PEMISAHAN ROLE =================
            if user.is_staff:
                return redirect('accounts:admin_dashboard')
            else:
                return redirect('accounts:dashboard')

        else:
            messages.error(request, "Password salah.")

    return render(request, 'accounts/login.html')
 
 # === admin_dashboard_view ===
@staff_member_required(login_url='accounts:login')
def admin_dashboard_view(request):
    context = {
        'total_users': User.objects.filter(is_staff=False).count(),
        'total_admins': User.objects.filter(is_staff=True).count(),
        'total_bmi': BMIResult.objects.count(),
        'total_mealplan': WeeklyMealPlan.objects.count(),
        'total_mental': MentalHealthLog.objects.count(),
        'latest_bmi': BMIResult.objects.order_by('-created_at')[:5],
    }

    return render(request, 'accounts/admin_dashboard.html', context)

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

@login_required(login_url='accounts:login')
def bmi_view(request):
    bmi = None
    kategori = None
    rekomendasi = []
    penyakit = None


    if request.method == 'POST':
        try:
            berat = float(request.POST.get('berat'))
            tinggi_cm = float(request.POST.get('tinggi'))
            tinggi = tinggi_cm / 100
            penyakit = request.POST.get('penyakit')

            bmi = berat / (tinggi ** 2)

            # ================= KATEGORI BMI =================
            if bmi < 18.5:
                kategori = "Kurus"
                rekomendasi += [
                    "Makan lebih sering dengan porsi kecil.",
                    "Makanan tinggi protein seperti telur, ayam, ikan.",
                    "Tambahkan kalori sehat seperti alpukat dan kacang-kacangan."
                ]

            elif 18.5 <= bmi < 25:
                kategori = "Normal (Ideal)"
                rekomendasi += [
                    "Pertahankan pola makan seimbang.",
                    "Rutin olahraga minimal 3x seminggu.",
                    "Perbanyak minum air putih."
                ]

            elif 25 <= bmi < 30:
                kategori = "Overweight"
                rekomendasi += [
                    "Kurangi konsumsi gula dan gorengan.",
                    "Makan lebih banyak sayur dan buah.",
                    "Lakukan olahraga ringan secara rutin."
                ]

            else:
                kategori = "Obesitas"
                rekomendasi += [
                    "Kurangi makanan tinggi kalori dan lemak.",
                    "Tingkatkan aktivitas fisik harian.",
                    "Pertimbangkan konsultasi dengan ahli gizi."
                ]

            # ================= PENYAKIT =================
            if penyakit == "diabetes":
                rekomendasi += [
                    "Hindari makanan manis dan minuman gula.",
                    "Pilih karbohidrat kompleks seperti beras merah.",
                    "Perbanyak sayuran hijau."
                ]

            elif penyakit == "hipertensi":
                rekomendasi += [
                    "Kurangi konsumsi garam.",
                    "Hindari makanan kemasan dan instan.",
                    "Perbanyak buah dan sayur."
                ]

            elif penyakit == "kolesterol":
                rekomendasi += [
                    "Kurangi makanan tinggi lemak jenuh.",
                    "Konsumsi oatmeal, ikan, dan kacang-kacangan."
                ]

            elif penyakit == "asam_urat":
                rekomendasi += [
                    "Hindari jeroan, seafood tinggi purin, dan daging merah.",
                    "Minum air putih banyak setiap hari."
                ]

            # ================= SIMPAN KE DATABASE =================
            BMIResult.objects.create(
                user=request.user,
                berat=berat,
                tinggi=tinggi * 100,  # balik ke cm
                bmi=round(bmi, 2),
                kategori=kategori,
                riwayat_input=penyakit or "",
                penyakit_terdeteksi=penyakit or "",
                rekomendasi=", ".join(rekomendasi)
)
            
            print("BMI DISIMPAN:", request.user.username, round(bmi, 2))



            # ================= SIMPAN KE SESSION =================
            request.session['penyakit'] = penyakit
            request.session['kategori_bmi'] = kategori

            return redirect('accounts:dashboard')

        except (ValueError, ZeroDivisionError):
            messages.error(request, "Input tidak valid. Masukkan angka dengan benar.")

    return render(request, 'accounts/bmi.html', {
        'bmi': bmi,
        'kategori': kategori,
        'penyakit': penyakit,
        'rekomendasi': rekomendasi
    })

@login_required(login_url='accounts:login')
def logout_view(request):
    logout(request)
    messages.success(request, "Berhasil logout.")
    return redirect('accounts:login')

@login_required
def monitor_view(request):
    if request.method == "POST":
        score = request.POST.get("score")
        kondisi = request.POST.get("kondisi")

        MentalHealthLog.objects.create(
            user=request.user,
            score=score,
            kondisi=kondisi
        )

        return JsonResponse({"status": "ok"})

    return render(request, 'accounts/monitor.html')

@login_required(login_url='accounts:login')
def tips_view(request):
    today = date.today()
    week = today.isocalendar()[1]
    year = today.year

    meal_plan = WeeklyMealPlan.objects.filter(
        user=request.user,
        week=week,
        year=year
    ).first()

    if request.method == 'POST':
        kondisi = request.POST.get('kondisi_kesehatan')
        alergi = request.POST.get('alergi_makanan')

        if meal_plan:
            # UPDATE
            meal_plan.kondisi_kesehatan = kondisi
            meal_plan.alergi_makanan = alergi
            meal_plan.save()
        else:
            # CREATE
            WeeklyMealPlan.objects.create(
                user=request.user,
                kondisi_kesehatan=kondisi,
                alergi_makanan=alergi,
                week=week,
                year=year
            )

        return redirect('accounts:dashboard')

    return render(request, 'accounts/weaklymeal.html', {
        'meal_plan': meal_plan
    })

@login_required(login_url='accounts:login')
def dashboard_view(request):
    last_bmi = BMIResult.objects.filter(user=request.user).last()
    target = None
        # ===== RIWAYAT BMI 7 DATA TERAKHIR =====
    weekly_logs = BMIResult.objects.filter(
        user=request.user
    ).order_by('-created_at')[:7]

    # ===================== TARGET HARIAN  =====================
    meal_plan = WeeklyMealPlan.objects.filter(user=request.user).last()

    if last_bmi:
        tinggi_m = last_bmi.tinggi / 100

        berat_ideal = round(22 * (tinggi_m ** 2), 1)
        progress_berat = round((last_bmi.berat / berat_ideal) * 100, 0)
        progress_berat = min(progress_berat, 100)

        kalori_target = round(last_bmi.berat * 30)
        kalori_harian = round(kalori_target * 0.7)
        progress_kalori = round((kalori_harian / kalori_target) * 100, 0)

        target = {
            "berat_sekarang": last_bmi.berat,
            "berat_ideal": berat_ideal,
            "progress_berat": progress_berat,
            "kalori_harian": kalori_harian,
            "kalori_target": kalori_target,
            "progress_kalori": progress_kalori,
        }

        return render(request, 'accounts/dashboard.html', {
        'last_bmi': last_bmi,
        'target': target,
        'weekly_logs': weekly_logs,
        'meal_plan': meal_plan,
    })


    # =====================  TAMBAHAN: PROGRES MINGGUAN =====================
    seminggu_lalu = timezone.now() - timedelta(days=7)

    weekly_logs = BMIResult.objects.filter(
        user=request.user,
        created_at__gte=seminggu_lalu
    ).order_by("created_at")

    return render(request, 'accounts/dashboard.html', {
        'last_bmi': last_bmi,
        'target': target,
        'weekly_logs': weekly_logs,  
    })

@login_required(login_url='accounts:login')
def weekly_meal_view(request):
    today = date.today()
    week = today.isocalendar()[1]
    year = today.year

    meal_plan = WeeklyMealPlan.objects.filter(
        user=request.user,
        week=week,
        year=year
    ).first()

    if request.method == "POST":
        kondisi = request.POST.get("kondisi_kesehatan")
        alergi = request.POST.get("alergi_makanan")

        WeeklyMealPlan.objects.update_or_create(
            user=request.user,
            week=week,
            year=year,
            defaults={
                "kondisi_kesehatan": kondisi,
                "alergi_makanan": alergi
            }
        )

        messages.success(request, "Weekly Meal Plan berhasil disimpan 💾")
        return redirect("accounts:dashboard")

    return render(request, "accounts/weaklymeal.html", {
        "meal_plan": meal_plan
    })

def chatbot_api(request):
    user_msg = request.GET.get('msg', '').lower()

    # RULE BOT
    if "halo" in user_msg or "hi" in user_msg:
        reply = "Halo! Ada yang bisa Medicheck bantu hari ini?"
    elif "bmi" in user_msg:
        reply = "Untuk hitung BMI, kamu bisa masuk ke menu BMI ya!"
    elif "makan apa" in user_msg:
        reply = "Coba konsumsi makanan bergizi: sayur, buah, protein, dan air putih."
    elif "obat" in user_msg:
        reply = "Gunakan obat sesuai anjuran dokter. Ada keluhan tertentu?"
    elif "tips" in user_msg:
        reply = "Tips kesehatan ada di menu Tips ya!"
    else:
        reply = "Aku belum mengerti pertanyaanmu, coba ulangi ya 😊"

    return JsonResponse({"reply": reply})



