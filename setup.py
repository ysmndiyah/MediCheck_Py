import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db.sqlite3"
DATA_FILE = BASE_DIR / "data.json"

def run_command(command, description):
    """Jalankan perintah terminal"""
    print(f"\n⚙️  {description} ...")
    try:
        subprocess.check_call(command, shell=True)
        print(f"✅ {description} berhasil.\n")
    except subprocess.CalledProcessError:
        print(f"❌ Gagal menjalankan: {description}")

def main():
    print("=== 🚀 Setup Otomatis MediCheck Lokal ===")

    # 1. Pastikan berada di direktori proyek
    os.chdir(BASE_DIR)

    # 2. Buat virtual environment (opsional)
    if not os.path.exists("venv"):
        run_command("python -m venv venv", "Membuat virtual environment")
        print("💡 Jalankan: venv\\Scripts\\activate (Windows) atau source venv/bin/activate (Mac/Linux)")

    # 3. Install dependencies
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt", "Menginstal dependencies")

    # 4. Cek database
    if not DB_PATH.exists():
        run_command("python manage.py migrate", "Menjalankan migrasi database")

        # 5. Jika punya file data.json, restore datanya
        if DATA_FILE.exists():
            run_command("python manage.py loaddata data.json", "Memuat data awal dari data.json")

        # 6. Membuat superuser otomatis (optional)
        print("👤 Membuat superuser admin default...")
        subprocess.call([
            sys.executable, "manage.py", "shell", "-c",
            (
                "from django.contrib.auth.models import User; "
                "User.objects.create_superuser('admin', 'admin@example.com', 'admin123') "
                "if not User.objects.filter(username='admin').exists() else print('Admin sudah ada')"
            )
        ])
        print("✅ Superuser dibuat (username: admin | password: admin123)")

    else:
        print("💾 Database sudah ada, skip migrate & superuser creation.")

    print("\n🎉 Setup selesai! Jalankan server dengan:\n   python manage.py runserver\n")

if __name__ == "__main__":
    main()
