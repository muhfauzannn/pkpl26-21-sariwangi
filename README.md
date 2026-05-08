# E-Voting System — PKPL Kelompok 21 (Sariwangi)

**Tugas 3 — Secure Coding Implementation**
Pengantar Keamanan Perangkat Lunak — Genap 2025/2026

---

## 1. Dokumen Pekerjaan

### 1.1 Deskripsi Aplikasi

**Skenario:** E-Voting System — Sistem pemungutan suara berbasis web yang digunakan untuk pendaftaran calon, pemungutan suara, dan rekapitulasi hasil pemilu secara digital.

**Fitur yang Diimplementasikan:**

| Modul | Fitur Utama                                                                        |
| ----- | ---------------------------------------------------------------------------------- |
| Auth  | Login, logout, register, role-based access control, rate limit, session security   |
| Pemilih | CRUD data pemilih, validasi NIK/NPM/email, status sudah/belum memilih           |
| Paslon | Pendaftaran paslon, input visi-misi, verifikasi/approve/reject oleh pengawas     |
| Voting | Daftar paslon, submit vote, cegah double voting, validasi eligibility            |
| Rekap  | Hasil voting, jumlah suara per paslon, audit log, dashboard pengawas            |

**Peran Pengguna:**

| Role            | Deskripsi                                               |
| --------------- | ------------------------------------------------------- |
| Pemilih         | Melakukan voting terhadap paslon                        |
| Paslon          | Mendaftar sebagai kandidat pemilu                       |
| Pengawas Pemilu | Melakukan verifikasi paslon dan monitoring hasil voting |

**Stack Teknologi:**

| Komponen          | Teknologi              |
| ----------------- | ---------------------- |
| Backend Framework | Django                 |
| Database          | SQLite                 |
| Frontend          | HTML, CSS              |
| Authentication    | Session-based          |
| Password Hashing  | PBKDF2                 |
| ORM               | Django ORM             |

---

### 1.2 Implementasi Secure Coding

#### A. Code Injection Prevention (CWE-94: Code Injection / CWE-20: Improper Input Validation)

**Vulnerability:** Input pengguna yang tidak divalidasi bisa menyebabkan eksekusi kode berbahaya atau XSS (Cross-Site Scripting).

**Vulnerable:**

```python
# Input langsung digunakan tanpa validasi atau sanitasi
username = request.POST['username']
user = User.objects.get(username=username)
```

**Secure:**

```python
# Input divalidasi dan disanitasi melalui Django Form
class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )

    def clean_username(self):
        return self.cleaned_data["username"].strip()
```

**Teknik Mitigasi:**

- Seluruh input pengguna divalidasi melalui Django Forms
- **Authentication module** (`apps/authentication/forms.py`):
  - Username: divalidasi dengan `UnicodeUsernameValidator`, dicek uniqueness (case-insensitive), di-strip whitespace
  - Email: divalidasi format email (`EmailField`), dicek uniqueness (case-insensitive)
  - Password: konfirmasi password wajib cocok dan divalidasi melalui Django password validators
  - Role: dibatasi hanya pilihan yang valid (allowlist, bukan free text)
- **Voters module** (`apps/voters/forms.py`):
  - NIK: validasi regex 16 digit angka (`^\d{16}$`)
  - NPM: validasi hanya digit angka
  - Email: validasi format + uniqueness (case-insensitive, exclude self on update)
  - Semua field teks di-strip whitespace (`clean_full_name`, `clean_faculty`, dll)
- **Candidates module** (`apps/candidates/forms.py`):
  - Nama paslon: di-strip whitespace
  - Visi: minimal 10 karakter
  - Misi: minimal 10 karakter
  - Anggota paslon: inline formset dengan validasi nama dan role (di-strip)
- Django template engine otomatis melakukan HTML escaping pada output, mencegah XSS
- Django ORM mencegah SQL injection secara otomatis

---

#### B. Broken Authentication Mitigation (CWE-307: Improper Restriction of Excessive Authentication Attempts / CWE-256: Plaintext Storage of a Password / CWE-613: Session Expiration)

**Vulnerability:** Attacker bisa brute-force login, password disimpan tanpa hashing, atau session tidak dikelola dengan aman.

**Vulnerable:**

```python
# Password dibandingkan langsung (plaintext)
if password == stored_password:
    login(user)

# Tidak ada rate limiting
def login_view(request):
    user = authenticate(request, username=username, password=password)
    # langsung login tanpa batasan percobaan
```

**Secure:**

```python
# Password hashing via PBKDF2 (Django default)
user = User.objects.create_user(username=username, password=password)
# password otomatis di-hash, tidak pernah disimpan plaintext

# Rate limiting dengan lockout
LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW_MINUTES = 15

def is_account_locked(username, ip_address):
    return get_recent_failed_attempts(username, ip_address) >= LOCKOUT_THRESHOLD
```

**Teknik Mitigasi:**

1. **Password Hashing (PBKDF2):**
   - Menggunakan PBKDF2 dengan salt melalui password hasher bawaan Django
   - Konfigurasi eksplisit di `config/settings/base.py`:
   ```python
   PASSWORD_HASHERS = [
       "django.contrib.auth.hashers.PBKDF2PasswordHasher",
       "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
   ]
   ```
   - User dibuat melalui `User.objects.create_user()` — tidak pernah menyimpan plaintext

2. **Rate Limiting / Lockout:**
   - Maksimal 5 kali percobaan login gagal dalam 15 menit per username+IP (`apps/authentication/services.py`)
   - Setelah 5x gagal, akun terkunci sementara selama 15 menit
   - Setiap percobaan login dicatat di model `LoginAttempt`
   - Error message generik ("Username atau password salah") — tidak mengungkapkan apakah username ada

3. **Session Security:**
   ```python
   SESSION_COOKIE_AGE = 1800              # 30 menit
   SESSION_COOKIE_HTTPONLY = True          # JavaScript tidak bisa akses cookie
   SESSION_COOKIE_SAMESITE = "Lax"         # Proteksi dari CSRF cross-site
   SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Session berakhir saat browser ditutup
   ```
   - Logout via POST request saja (bukan GET) untuk mencegah CSRF-triggered logout
   - Django `logout()` memflush session secara lengkap

4. **Least Privilege:**
   - Registrasi hanya memperbolehkan role `pemilih` dan `paslon` — `pengawas` harus dibuat via Django admin
   - Role-Based Access Control Middleware membatasi akses berdasarkan role:
     - `pengawas`: semua path aplikasi dan dashboard audit
     - `pemilih`: `/voting/`, `/candidates/` hanya paslon approved/read-only, `/auth/logout/`
     - `paslon`: `/candidates/` untuk data paslonnya sendiri, `/voting/results/`, `/auth/logout/`
   - User yang mengakses path di luar haknya mendapat `403 Forbidden`

---

#### C. CSRF Protection (CWE-352: Cross-Site Request Forgery)

**Vulnerability:** Attacker bisa memalsukan request dari user yang sudah terautentikasi untuk melakukan aksi tanpa sepengetahuan user.

**Vulnerable:**

```html
<!-- Form tanpa CSRF token -->
<form method="POST" action="/auth/logout/">
    <button type="submit">Logout</button>
</form>
```

**Secure:**

```html
<!-- Form dengan CSRF token -->
<form method="POST">
    {% csrf_token %}
    <button type="submit">Logout</button>
</form>
```

**Teknik Mitigasi:**

- `CsrfViewMiddleware` aktif secara global di `MIDDLEWARE` (`config/settings/base.py`)
- Semua form yang melakukan operasi write (POST/PUT/DELETE) menggunakan `{% csrf_token %}`
- CSRF token divalidasi di sisi server sebelum memproses request
- Logout hanya menerima POST request (bukan GET)
- Cookie CSRF dan session dilindungi dengan `HttpOnly` dan `SameSite=Lax`
- **Candidates module** (`apps/candidates/templates/`):
  - Form pendaftaran paslon menggunakan `{% csrf_token %}`
  - Tombol approve/reject di detail page masing-masing dalam `<form method="POST">` dengan CSRF token
  - Satu paslon tidak bisa mendaftar dua kali — view mengecek `Candidate.objects.filter(user=request.user).exists()`
- **Voting module** (`apps/voting/templates/`):
  - Form voting menggunakan `{% csrf_token %}`
  - Radio button selection untuk memilih paslon
  - Submit vote hanya via POST request

---

#### D. SQL Injection Prevention (CWE-89: SQL Injection)

**Vulnerability:** Input pengguna yang tidak tersanitasi bisa memanipulasi query database.

**Vulnerable:**

```python
# Raw SQL dengan string concatenation
query = "SELECT * FROM users WHERE username='" + username + "'"
cursor.execute(query)
```

**Secure:**

```python
# Menggunakan Django ORM
user = User.objects.get(username=username)

# Atau parameterized query jika raw SQL diperlukan
cursor.execute("SELECT * FROM users WHERE username = %s", [username])
```

**Teknik Mitigasi:**

- Seluruh operasi database menggunakan Django ORM — tidak ada raw SQL
- Django ORM otomatis menggunakan parameterized queries
- Contoh query yang aman:
  ```python
  # Authentication module
  User.objects.filter(username__iexact=username).exists()
  LoginAttempt.objects.filter(user__username=username, success=False).count()

  # Voters module
  Voter.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
  Voter.objects.all().order_by("-created_at")

  # Candidates module — semua operasi menggunakan ORM
  Candidate.objects.filter(user=request.user).exists()
  Candidate.objects.filter(candidate_number__isnull=False).order_by("-candidate_number")

  # Voting module — anti double voting via unique constraint
  Vote.objects.filter(voter=request.user).exists()
  Vote.objects.create(voter=user, candidate=candidate)
  Vote.objects.count()

  # Dashboard module — audit logging
  AuditLog.objects.create(user=request.user, action=action, description=desc, ip_address=ip)
  AuditLog.objects.all()[:100]
  ```
- Input pengguna tidak pernah digabungkan langsung ke string query
- Koneksi database dibatasi ke SQLite lokal (`db.sqlite3`), tanpa dukungan konfigurasi database eksternal
- **Audit logging** (`apps/dashboard/services.py`): Setiap aksi penting (login, logout, vote, CRUD pemilih, approve/reject paslon) dicatat ke model `AuditLog` dengan user, action, description, IP address, dan timestamp


### 1.3 Screenshot Aplikasi
---
#### Authentication

**Login**
![Login](screenshots/Login_-_E-Voting_System.png)

**Login Gagal - Akun Terkunci (5x Salah)**
![Login Salah](screenshots/Login_Salah___5x_Akun_Locked.png)

**Registrasi**
![Registrasi](screenshots/Registrasi_-_E-Voting_System.png)

---

#### View sebagai Pengawas

**Login Berhasil**
![Login Berhasil](screenshots/pengawas_login_success.png)

**Login Gagal**
![Login Gagal](screenshots/pengawas_login_gagal.png)

**Dashboard Pengawas**
![Dashboard Pengawas](screenshots/pengawas_dashboard_pengawas.png)

**Kelola Data Pemilih**
![Kelola Data Pemilih](screenshots/pengawas_kelola_pemilih.png)

**Tambah Pemilih**
![Tambah Pemilih](screenshots/pengawas_tambah_pemilih.png)

**Validasi Input NIK**
![Validasi Input NIK](screenshots/pengawas_validasi_input_nik.png)

**Tambah Pemilih - Berhasil**
![Tambah Pemilih Berhasil](screenshots/pengawas_success_tambah_pemilih.png)

**Kelola Paslon**
![Kelola Paslon](screenshots/pengawas_kelola_paslon.png)

**Detail Paslon 1**
![Detail Paslon 1](screenshots/pengawas_detail_paslon1.png)

**Detail Paslon 2**
![Detail Paslon 2](screenshots/pengawas_detail_paslon2.png)

**Detail Paslon 3**
![Detail Paslon 3](screenshots/pengawas_detail_paslon3.png)

**Hasil Suara**
![Hasil Suara](screenshots/pengawas_hasil_suara.png)

**Audit Log**
![Audit Log](screenshots/pengawas_audit_log.png)

---

#### View sebagai Paslon

**Registrasi Paslon**
![Registrasi Paslon](screenshots/Registrasi_Paslon_-_E-Voting_System.png)

**Daftar Paslon - Menunggu Verifikasi**
![Daftar Paslon Menunggu](screenshots/Daftar_Paslon_Menunggu_-_E-Voting_System.png)

**Daftar Paslon - Disetujui**
![Daftar Paslon Disetujui](screenshots/Daftar_Paslon_Disetujui_-_E-Voting_System.png)

**Rekapitulasi Hasil Suara**
![Rekapitulasi Hasil](screenshots/Rekapitulasi_Hasil_-_E-Voting_System.png)

---

#### View sebagai Pemilih

**Daftar Paslon**
![Daftar Paslon](screenshots/Daftar_Paslon_-_E-Voting_System.png)

**Paslon 1 - Harapan Bangsa**
![Paslon Harapan Bangsa](screenshots/Paslon_Harapan_Bangsa_-_E-Voting_System.png)

**Paslon 2 - Maju Bersama**
![Paslon Maju Bersama](screenshots/Paslon_Maju_Bersama_-_E-Voting_System.png)

**Paslon 3 - Untuk Rakyat**
![Paslon Untuk Rakyat](screenshots/Paslon_Untuk_Rakyat_-_E-Voting_System.png)

**Surat Suara**
![Surat Suara](screenshots/Surat_Suara_-_E-Voting_System.png)

**Pilih Paslon 1**
![Pilih 1](screenshots/Surat_Suara_-_E-Voting_System__pilih_1_.png)

**Pilih Paslon 2**
![Pilih 2](screenshots/Surat_Suara_-_E-Voting_System__pilih_2_.png)

**Pilih Paslon 3**
![Pilih 3](screenshots/Surat_Suara_-_E-Voting_System__pilih_3_.png)

**Konfirmasi Pilihan**
![Konfirmasi](screenshots/Surat_Suara_-_E-Voting_System__pilih_paslon_.png)

**Voting Berhasil**
![Voting Berhasil](screenshots/Voting_Berhasil_-_E-Voting_System.png)

**Hasil Voting**
![Hasil Voting](screenshots/Hasil_Voting_-_E-Voting_System__lihat_hasil_.png)

---

#### Security

**Password Ter-hash di Database**
![Password Hash](screenshots/Password_ter-hash_di_Database.png)

Bagian security lainnya akan kami demokan di video.

---

### 1.4 Hasil Test-Case

Pengujian dilakukan dengan Django test client dan system check pada settings development serta production.

```bash
source .venv/bin/activate
python manage.py test --settings=config.settings.development
coverage run manage.py test --settings=config.settings.development
coverage report -m
python manage.py check --settings=config.settings.development
SECRET_KEY=check-secret ALLOWED_HOSTS=localhost,127.0.0.1 python manage.py check --settings=config.settings.production
```

Log hasil pengujian:

```text
Found 46 test(s).
Ran 46 tests in 13.232s
OK
TOTAL 707 0 100%
System check identified no issues (0 silenced).
System check identified no issues (0 silenced).
```

#### Test Case — Modul 1: Authentication & Authorization

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Login dengan kredensial benar                  | Berhasil login, redirect ke halaman sesuai role             | PASS |
| 2  | Login dengan password salah                    | Muncul error "Username atau password salah"                 | PASS |
| 3  | Rate limiting (lockout setelah 5x gagal)       | Muncul error "Akun sementara dikunci. Coba lagi dalam 15 menit." | PASS |
| 4  | Registrasi dengan role pengawas                | Form tidak memiliki opsi "Pengawas", request ditolak        | PASS |
| 5  | Akses halaman protected tanpa login            | Diredirect ke `/auth/login/`                                | PASS |
| 6  | CSRF token pada form                           | Form mengandung `csrfmiddlewaretoken`, request tanpa token ditolak (403) | PASS |
| 7  | Password disimpan dengan hashing               | Nilai password tersimpan sebagai hash PBKDF2, bukan plaintext | PASS |
| 8  | Password lemah saat registrasi                 | Ditolak oleh Django password validators                     | PASS |

#### Test Case — Modul 2: Manajemen Data Pemilih

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Tambah data pemilih dengan data valid          | Data tersimpan, redirect ke daftar pemilih, muncul pesan sukses | PASS |
| 2  | Tambah pemilih dengan NIK kurang dari 16 digit | Muncul error "NIK harus terdiri dari 16 digit angka."       | PASS |
| 3  | Tambah pemilih dengan NPM mengandung huruf     | Muncul error "NPM harus terdiri dari digit angka."          | PASS |
| 4  | Tambah pemilih dengan email duplikat           | Muncul error "Email sudah digunakan oleh pemilih lain."     | PASS |
| 5  | Edit data pemilih                              | Data berhasil diperbarui, pesan sukses muncul               | PASS |
| 6  | Hapus data pemilih                             | Data terhapus, pesan sukses muncul                          | PASS |
| 7  | Akses /voters/ oleh pemilih (non-pengawas)     | Ditolak (403 Forbidden) karena middleware RBAC              | PASS |
| 8  | Input dengan karakter berbahaya (XSS attempt)  | Karakter di-escape oleh Django template, tidak dieksekusi   | PASS |

#### Test Case — Modul 3: Pendaftaran & Verifikasi Paslon

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Paslon mendaftar dengan data lengkap           | Data tersimpan, redirect ke daftar paslon, status "Menunggu Verifikasi" | PASS |
| 2  | Paslon mendaftar dengan visi < 10 karakter     | Muncul error "Visi terlalu pendek (minimal 10 karakter)."  | PASS |
| 3  | Paslon mendaftar dua kali                      | Diredirect ke daftar paslon, pesan "Anda sudah terdaftar"  | PASS |
| 4  | Pengawas menyetujui paslon                     | Status berubah ke "Disetujui", nomor paslon ditetapkan otomatis | PASS |
| 5  | Pengawas menolak paslon                        | Status berubah ke "Ditolak"                                 | PASS |
| 6  | Pemilih mencoba akses /candidates/register/    | Ditolak (403 Forbidden) karena RBAC                         | PASS |
| 7  | Approve/reject tanpa CSRF token                | Request ditolak (403 CSRF verification failed)             | PASS |
| 8  | Paslon yang sudah diapprove di-approve lagi    | Pesan "Paslon sudah diverifikasi sebelumnya"               | PASS |
| 9  | Pemilih melihat daftar/detail paslon           | Hanya paslon approved yang ditampilkan                      | PASS |

#### Test Case — Modul 4: Pemungutan Suara

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Pemilih submit vote untuk paslon yang disetujui | Vote tercatat, redirect ke halaman sukses                  | PASS |
| 2  | Pemilih mencoba vote dua kali                  | Diredirect ke results, pesan "Anda sudah melakukan voting"  | PASS |
| 3  | Paslon mencoba akses /voting/                  | Ditolak (403 Forbidden) karena middleware RBAC              | PASS |
| 4  | Vote tanpa CSRF token                          | Request ditolak (403 CSRF verification failed)             | PASS |
| 5  | Vote tanpa memilih paslon                      | Muncul error "Pilih salah satu paslon."                    | PASS |
| 6  | Hasil voting menampilkan jumlah suara per paslon | Vote count ditampilkan dengan progress bar                | PASS |
| 7  | IntegrityError saat double vote (race condition) | Ditangkap oleh try/except, pesan error ditampilkan        | PASS |
| 8  | Akses rekap tanpa login                        | Diredirect ke halaman login                                | PASS |

#### Test Case — Modul 5: Rekapitulasi & Audit

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Dashboard menampilkan total suara dan rekapitulasi | Angka benar, progress bar sesuai proporsi                | PASS |
| 2  | Audit log mencatat login                       | Tercatat dengan username, IP, dan timestamp                | PASS |
| 3  | Audit log mencatat logout                      | Tercatat dengan username dan timestamp                     | PASS |
| 4  | Audit log mencatat voter create/update/delete  | Tercatat dengan nama pemilih dan NIK                       | PASS |
| 5  | Audit log mencatat candidate approve/reject    | Tercatat dengan nama paslon dan nomor paslon               | PASS |
| 6  | Audit log mencatat vote                        | Tercatat dengan username dan nama paslon yang dipilih      | PASS |
| 7  | Halaman audit log menampilkan 100 log terbaru  | Tabel berisi waktu, user, IP, aksi, dan detail             | PASS |

---

## 2. Source Code

### Instalasi

1. Clone repository:

```bash
git clone https://gitlab.cs.ui.ac.id/pkpl26/21-sariwangi/pkpl26_21_sariwangi.git
cd PKPL26_21_sariwangi
```

2. Buat virtual environment dan install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

3. Copy `.env.example` ke `.env`:

```bash
cp .env.example .env
```

4. Jalankan migrasi dan buat superuser dengan role pengawas:

```bash
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@example.com
python manage.py shell -c "from apps.authentication.models import User; User.objects.filter(username='admin').update(role=User.Role.PENGAWAS)"
```

5. (Opsional) Seed database SQLite dengan data contoh:

```bash
python manage.py seed --clean --voters 25
```

Opsi seeder:

| Flag | Default | Deskripsi |
| --- | --- | --- |
| `--voters N` | 25 | Jumlah pemilih yang dibuat |
| `--voted 0.75` | 0.75 | Persentase pemilih yang sudah vote (0.0–1.0) |
| `--clean` | - | Hapus semua data sebelum seeding |

Data yang dibuat oleh seeder:

| Data | Detail |
| --- | --- |
| **Pengawas** | `pengawas` / `SariwangiDemo123!` |
| **3 Paslon** | `paslon1`, `paslon2`, `paslon3` / `SariwangiDemo123!` — status approved, dengan anggota |
| **25 Pemilih** | `pemilih1`–`pemilih25` / `SariwangiDemo123!` — terhubung ke Voter profile, 75% sudah vote |

Password di atas hanya kredensial demo lokal yang dibuat oleh seeder. Password tetap disimpan sebagai hash PBKDF2 di database.

6. Jalankan development server:

```bash
python manage.py runserver
```

7. Akses aplikasi di `http://127.0.0.1:8000/`

Catatan database: aplikasi hanya menggunakan SQLite lokal melalui `db.sqlite3`. File tersebut disertakan di repository sesuai ketentuan tugas, sedangkan konfigurasi database eksternal tidak didukung.

### Struktur Project

```
PKPL26_21_sariwangi/
├── config/                 # Konfigurasi project
│   ├── settings/
│   │   ├── base.py         # Settings utama (session security, auth, dll)
│   │   ├── development.py  # Dev overrides (DEBUG=True)
│   │   └── production.py   # Prod overrides (HTTPS, secure cookies)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── authentication/     # Modul 1: Auth & Authorization
│   ├── voters/             # Modul 2: Manajemen Data Pemilih
│   ├── candidates/         # Modul 3: Pendaftaran & Verifikasi Paslon
│   ├── voting/             # Modul 4: Pemungutan Suara
│   └── dashboard/          # Modul 5: Rekapitulasi & Audit
├── templates/              # Template level project
├── static/                 # Static files level project
├── media/                  # User-uploaded files
├── db.sqlite3              # Database SQLite lokal
├── manage.py
├── requirements.txt
└── README.md
```

---

## 3. Video Demo & Penjelasan

**Video URL:** `https://youtu.be/a9cHudECDqE`

**Konten Video:**
1. Demo aplikasi secara fungsional (maks. 2 menit)
2. Demonstrasi pengujian berdasarkan test case dan hasilnya
3. Penjelasan teknik mitigasi yang dipilih beserta alasannya
