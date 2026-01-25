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
from django.views.decorators.csrf import csrf_exempt
import json
import os
from openai import OpenAI

print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    sumber = None

    if request.method == 'POST':
        try:
            berat = float(request.POST.get('berat'))
            tinggi_cm = float(request.POST.get('tinggi'))
            penyakit = request.POST.get('penyakit', '').lower()

            tinggi = tinggi_cm / 100
            bmi = round(berat / (tinggi ** 2), 1)

            # ===== KATEGORI BMI =====
            if bmi < 18.5:
                kategori = "Kurus"
                rekomendasi = [
                    "Makan lebih sering dengan porsi kecil",
                    "Perbanyak protein",
                    "Tambahkan kalori sehat"
                ]
                sumber = "https://www.who.int"

            elif bmi < 25:
                kategori = "Normal (Ideal)"
                rekomendasi = [
                    "Pertahankan pola makan seimbang",
                    "Olahraga rutin",
                    "Cukup minum air putih"
                ]
                sumber = "https://www.who.int"

            elif bmi < 30:
                kategori = "Overweight"
                rekomendasi = [
                    "Kurangi gula dan gorengan",
                    "Perbanyak sayur dan buah",
                    "Aktivitas fisik teratur"
                ]
                sumber = "https://www.cdc.gov"

            else:
                kategori = "Obesitas"
                rekomendasi = [
                    "Kurangi makanan tinggi lemak",
                    "Tingkatkan aktivitas fisik",
                    "Konsultasi ahli gizi"
                ]
                sumber = "https://www.cdc.gov"

            # ===== PENYESUAIAN PENYAKIT =====
            if "asam lambung" in penyakit:
                rekomendasi.append("Hindari makanan pedas dan asam")
                sumber = "https://www.mayoclinic.org"

            # ===== SIMPAN DATABASE =====
            BMIResult.objects.create(
                user=request.user,
                berat=berat,
                tinggi=tinggi_cm,
                bmi=bmi,
                kategori=kategori,
                penyakit_terdeteksi=penyakit,
                rekomendasi=", ".join(rekomendasi)
            )

        except (ValueError, ZeroDivisionError):
            messages.error(request, "Input tidak valid. Masukkan angka dengan benar.")

    return render(request, 'accounts/bmi.html', {
        'bmi': bmi,
        'kategori': kategori,
        'penyakit': penyakit,
        'rekomendasi': rekomendasi,
        'sumber': sumber,
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
    today = date.today()
    week = today.isocalendar()[1]
    year = today.year

    last_bmi = BMIResult.objects.filter(user=request.user).last()

    weekly_logs = BMIResult.objects.filter(
        user=request.user
    ).order_by('-created_at')[:7]

    meal_plan = WeeklyMealPlan.objects.filter(
        user=request.user,
        week=week,
        year=year
    ).first()

    target = None

    if last_bmi:
        tinggi_m = last_bmi.tinggi / 100
        berat_ideal = round(22 * (tinggi_m ** 2), 1)
        progress_berat = min(round((last_bmi.berat / berat_ideal) * 100, 0), 100)

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

    if request.method == "POST":
        meal_plan_text = request.POST.get("meal_plan")

        WeeklyMealPlan.objects.update_or_create(
            user=request.user,
            week=week,
            year=year,
            defaults={"meal_plan": meal_plan_text}
        )

        messages.success(request, "✅ Weekly Meal Plan berhasil disimpan!")
        return redirect("accounts:tips")

    return render(request, "accounts/weaklymeal.html")

# ==== chatbot_api ====
@csrf_exempt
@login_required(login_url='accounts:login')
def chatbot_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"reply": "Pesan tidak boleh kosong."})

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Kamu adalah MediBot, asisten kesehatan digital. "
                            "Jawab dalam bahasa Indonesia yang sopan, ramah, dan edukatif. "
                            "Jangan memberikan diagnosis medis."
                        )
                    },
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=300
            )

            reply = response.choices[0].message.content
            return JsonResponse({"reply": reply})

        except Exception as e:
            if "quota" in str(e).lower():
             return JsonResponse({
            "reply": "Maaf, layanan AI sedang mencapai batas penggunaan. Silakan coba lagi nanti 🙏"
        })
    return JsonResponse({
        "reply": "MediBot sedang mengalami gangguan 😢"
    })


    return JsonResponse({"reply": "Metode tidak diizinkan."})

    



