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
| Frontend          | HTML, CSS, Inter + JetBrains Mono |
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
  - Password: konfirmasi password wajib cocok, divalidasi melalui Django password validators
  - Role: dibatasi hanya pilihan yang valid (allowlist, bukan free text)
- **Voters module** (`apps/voters/forms.py`):
  - NIK: validasi regex 16 digit angka (`^\d{16}$`)
  - NPM: validasi hanya digit angka
  - Email: validasi format + uniqueness (case-insensitive, exclude self on update)
  - Semua field teks di-strip whitespace (`clean_full_name`, `clean_faculty`, dll)
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
   - Menggunakan PBKDF2 dengan salt (200,000+ iterations)
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
     - `pengawas`: semua path
     - `pemilih`: `/voting/`, `/auth/logout/`
     - `paslon`: `/candidates/`, `/auth/logout/`
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
- Cookie `csrfmiddlewaretoken` dilindungi dengan `HttpOnly` dan `SameSite`

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

  # Voters module — semua CRUD menggunakan ORM
  Voter.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
  Voter.objects.all().order_by("-created_at")
  voter.delete()
  ```
- Input pengguna tidak pernah digabungkan langsung ke string query

---

### 1.3 Screenshot Aplikasi

> *Screenshot akan ditambahkan setelah seluruh modul selesai diimplementasi.*

<!-- Placeholder untuk screenshot:
- Halaman Login
- Halaman Register
- Dashboard sesuai role
- Halaman voting
- Halaman rekapitulasi
-->

---

### 1.4 Hasil Test-Case

> *Hasil test-case lengkap akan ditambahkan setelah seluruh modul selesai diimplementasi.*

#### Test Case — Modul 1: Authentication & Authorization

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Login dengan kredensial benar                  | Berhasil login, redirect ke halaman sesuai role             |        |
| 2  | Login dengan password salah                    | Muncul error "Username atau password salah"                 |        |
| 3  | Rate limiting (lockout setelah 5x gagal)       | Muncul error "Akun sementara dikunci. Coba lagi dalam 15 menit." |  |
| 4  | Registrasi dengan role pengawas                | Form tidak memiliki opsi "Pengawas", request ditolak        |        |
| 5  | Akses halaman protected tanpa login            | Diredirect ke `/auth/login/`                                |        |
| 6  | CSRF token pada form                           | Form mengandung `csrfmiddlewaretoken`, request tanpa token ditolak (403) | |

#### Test Case — Modul 2: Manajemen Data Pemilih

| No | Test Case                                      | Expected Result                                             | Status |
| -- | ---------------------------------------------- | ----------------------------------------------------------- | ------ |
| 1  | Tambah data pemilih dengan data valid          | Data tersimpan, redirect ke daftar pemilih, muncul pesan sukses |     |
| 2  | Tambah pemilih dengan NIK kurang dari 16 digit | Muncul error "NIK harus terdiri dari 16 digit angka."       |        |
| 3  | Tambah pemilih dengan NPM mengandung huruf     | Muncul error "NPM harus terdiri dari digit angka."          |        |
| 4  | Tambah pemilih dengan email duplikat           | Muncul error "Email sudah digunakan oleh pemilih lain."     |        |
| 5  | Edit data pemilih                              | Data berhasil diperbarui, pesan sukses muncul               |        |
| 6  | Hapus data pemilih                             | Data terhapus, pesan sukses muncul                          |        |
| 7  | Akses /voters/ oleh pemilih (non-pengawas)     | Ditolak (403 Forbidden) karena middleware RBAC              |        |
| 8  | Input dengan karakter berbahaya (XSS attempt)  | Karakter di-escape oleh Django template, tidak dieksekusi   |        |

---

## 2. Source Code

### Instalasi

1. Clone repository:

```bash
git clone https://gitlab.cs.ui.ac.id/<path-to-repo>/PKPL26_21_sariwangi.git
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

4. Jalankan migrasi dan buat superuser (pengawas):

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Jalankan development server:

```bash
python manage.py runserver
```

6. Akses aplikasi di `http://127.0.0.1:8000/`

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
├── manage.py
├── requirements.txt
└── README.md
```

---

## 3. Video Demo & Penjelasan

> *Link video akan ditambahkan setelah video selesai direkam.*

<!-- TODO: Upload video ke YouTube sebagai "Unlisted" dan taruh link di sini -->

**Video URL:** `https://youtu.be/XXXXXXX`

**Konten Video:**
1. Demo aplikasi secara fungsional (maks. 2 menit)
2. Demonstrasi pengujian berdasarkan test case dan hasilnya
3. Penjelasan teknik mitigasi yang dipilih beserta alasannya
