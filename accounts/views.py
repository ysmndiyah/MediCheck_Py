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
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetToken
from django.contrib.auth.decorators import user_passes_test

print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# === LOGIN DENGAN EMAIL ===
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # === CARI USER BERDASARKAN EMAIL ===
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Email tidak ditemukan.")
            return render(request, 'accounts/login.html')

        # === AUTENTIKASI ===
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            messages.success(
                request,
                f"Selamat datang, {user.first_name or user.username}!"
            )

            # === PEMISAHAN ROLE ===
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

# === REGISTER DENGAN EMAIL & NAMA LENGKAP ===
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

# accounts/views.py

@login_required(login_url='accounts:login')
def bmi_view(request):
    bmi = None
    kategori = None
    rekomendasi = []
    penyakit = None
    sumber = None

    if request.method == 'POST':
        try:
            # 1. AMBIL INPUT
            berat = float(request.POST.get('berat'))
            tinggi_cm = float(request.POST.get('tinggi'))
            usia = int(request.POST.get('usia'))
            gender = request.POST.get('gender')  # <--- AMBIL GENDER
            penyakit = request.POST.get('penyakit', '').lower()

            tinggi = tinggi_cm / 100
            bmi = round(berat / (tinggi ** 2), 1)

            # 2. KATEGORI BMI (UMUM)
            if bmi < 18.5:
                kategori = "Kurus"
                sumber = "https://www.who.int"
            elif bmi < 25:
                kategori = "Normal (Ideal)"
                sumber = "https://www.who.int"
            elif bmi < 30:
                kategori = "Overweight"
                sumber = "https://www.cdc.gov"
            else:
                kategori = "Obesitas"
                sumber = "https://www.cdc.gov"

            # 3. REKOMENDASI SPESIFIK BERDASARKAN GENDER & BMI ✨
            
            # --- SKENARIO LAKI-LAKI 👨 ---
            if gender == 'Laki-laki':
                if bmi < 18.5:
                    rekomendasi.append("Fokus latihan beban (gym) untuk massa otot")
                    rekomendasi.append("Tingkatkan asupan protein (dada ayam, telur, tempe)")
                elif bmi >= 25:
                    rekomendasi.append("Lakukan kardio intensitas tinggi (Lari/Futsal)")
                    rekomendasi.append("Kurangi nasi putih, perbanyak lauk protein")
                else:
                    rekomendasi.append("Jaga kebugaran dengan Push-up dan Sit-up rutin")

            # --- SKENARIO PEREMPUAN 👩 ---
            else:
                if bmi < 18.5:
                    rekomendasi.append("Pastikan asupan Zat Besi (bayam/hati ayam) tercukupi")
                    rekomendasi.append("Hindari diet ekstrem, makan teratur 3x sehari")
                elif bmi >= 25:
                    rekomendasi.append("Senam aerobik, Zumba, atau Yoga untuk bakar lemak")
                    rekomendasi.append("Kurangi makanan manis/boba/gorengan")
                else:
                    rekomendasi.append("Yoga atau Pilates untuk kelenturan tubuh")
            
            # 4. LOGIKA USIA (Pelengkap)
            if usia > 50:
                if gender == 'Perempuan':
                    rekomendasi.append("Wajib Kalsium tinggi untuk cegah Osteoporosis (pengeroposan tulang)")
                rekomendasi.append("Olahraga ringan: Jalan kaki pagi")
            
            elif usia < 18:
                rekomendasi.append("Tidur 8 jam untuk hormon pertumbuhan")

            # 5. PENYESUAIAN PENYAKIT
            if "asam lambung" in penyakit:
                rekomendasi.append("Makan porsi kecil tapi sering (5x sehari)")
                
            # 6. SIMPAN KE DATABASE
            BMIResult.objects.create(
                user=request.user,
                berat=berat,
                tinggi=tinggi_cm,
                usia=usia,
                gender=gender,  # <--- SIMPAN DATA GENDER
                bmi=bmi,
                kategori=kategori,
                penyakit_terdeteksi=penyakit,
                rekomendasi=", ".join(rekomendasi)
            )

        except (ValueError, ZeroDivisionError):
            messages.error(request, "Input tidak valid.")

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
    # 1. Inisialisasi Waktu
    today = date.today()
    iso_date = today.isocalendar()
    week, year = iso_date[1], today.year
    seminggu_lalu = timezone.now() - timedelta(days=7)

    # 2. Ambil Data dari Database
    last_bmi = BMIResult.objects.filter(user=request.user).last()
    meal_plan = WeeklyMealPlan.objects.filter(
        user=request.user, 
        week=week, 
        year=year
    ).first()
    
    # Mengambil log BMI selama 7 hari terakhir (diurutkan dari yang terlama ke terbaru untuk grafik)
    weekly_logs = BMIResult.objects.filter(
        user=request.user,
        created_at__gte=seminggu_lalu
    ).order_by("created_at")

    # 3. Logika Perhitungan Target
    target = None
    if last_bmi and last_bmi.tinggi > 0:
        # Hitung Berat Ideal (Rumus: 22 * tinggi_m^2)
        tinggi_m = last_bmi.tinggi / 100
        berat_ideal = round(22 * (tinggi_m ** 2), 1)
        
        # Hitung Target Kalori (Rumus: Berat * 30)
        kalori_target = round(last_bmi.berat * 30)
        kalori_harian = round(kalori_target * 0.7) # Contoh asumsi konsumsi saat ini

        # Hitung Persentase Progress (Dibatasi max 100%)
        progress_berat = min(round((last_bmi.berat / berat_ideal) * 100), 100) if berat_ideal > 0 else 0
        progress_kalori = min(round((kalori_harian / kalori_target) * 100), 100) if kalori_target > 0 else 0

        target = {
            "berat_sekarang": last_bmi.berat,
            "berat_ideal": berat_ideal,
            "progress_berat": progress_berat,
            "kalori_harian": kalori_harian,
            "kalori_target": kalori_target,
            "progress_kalori": progress_kalori,
        }

    # 4. Kirim ke Template (Hanya satu kali return render)
    context = {
        'last_bmi': last_bmi,
        'target': target,
        'weekly_logs': weekly_logs,
        'meal_plan': meal_plan,
    }
    return render(request, 'accounts/dashboard.html', context)

    # ===  TAMBAHAN: PROGRES MINGGUAN ===
    seminggu_lalu = timezone.now() - timedelta(days=7)

    weekly_logs = BMIResult.objects.filter( #django ORM mengelola database
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

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Buat atau Ambil Token
            token_obj, created = PasswordResetToken.objects.get_or_create(user=user)
            token_obj.generate_token() # Generate kode baru
            
            # Kirim Email
            subject = 'Kode Reset Password MediCheck'
            message = f'Kode OTP kamu adalah: {token_obj.token}'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
            
            # Simpan email di session biar tidak perlu ketik ulang
            request.session['reset_email'] = email
            messages.success(request, f"Kode telah dikirim ke {email}")
            return redirect('accounts:verify_otp')
            
        except User.DoesNotExist:
            messages.error(request, "Email tidak terdaftar.")
            
    return render(request, 'accounts/forgot_password.html')

# 2. HALAMAN INPUT KODE OTP
def verify_otp_view(request):
    if request.method == 'POST':
        kode_input = request.POST.get('otp')
        email = request.session.get('reset_email')
        
        try:
            user = User.objects.get(email=email)
            token_obj = PasswordResetToken.objects.get(user=user)
            
            if token_obj.token == kode_input:
                # KODE BENAR!
                return redirect('accounts:new_password')
            else:
                messages.error(request, "Kode salah!")
        except:
            messages.error(request, "Terjadi kesalahan.")

    return render(request, 'accounts/verify_otp.html')

# 3. HALAMAN BUAT PASSWORD BARU
def new_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:login')

    if request.method == 'POST':
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('confirm_password')
        
        if pass1 != pass2:
            messages.error(request, "Password tidak cocok.")
        else:
            user = User.objects.get(email=email)
            user.set_password(pass1) # Ubah password
            user.save()
            
            PasswordResetToken.objects.filter(user=user).delete()
            del request.session['reset_email'] # Bersihkan session
            
            messages.success(request, "Password berhasil diubah! Silakan login.")
            return redirect('accounts:login')

    return render(request, 'accounts/new_password.html')

    
    



