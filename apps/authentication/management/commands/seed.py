import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.authentication.models import User
from apps.candidates.models import Candidate, CandidateMember
from apps.voters.models import Voter
from apps.voting.models import Vote


DEMO_PASSWORD = "SariwangiDemo123!"


class Command(BaseCommand):
    help = "Seed database with sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--voters",
            type=int,
            default=20,
            help="Number of voters to create (default 20)",
        )
        parser.add_argument(
            "--voted",
            type=float,
            default=0.75,
            help="Fraction of voters that already voted (default 0.75)",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete all existing data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        total_voters = options["voters"]
        vote_fraction = options["voted"]
        clean = options["clean"]

        if clean:
            Vote.objects.all().delete()
            CandidateMember.objects.all().delete()
            Candidate.objects.all().delete()
            Voter.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write("Cleared all existing data.")

        # --- Pengawas ---
        if not User.objects.filter(username="pengawas").exists():
            User.objects.create_user(
                username="pengawas",
                email="pengawas@evote.id",
                password=DEMO_PASSWORD,
                first_name="Pengawas",
                last_name="Pemilu",
                role="pengawas",
            )
            self.stdout.write(self.style.SUCCESS(f"Created pengawas ({DEMO_PASSWORD})"))
        else:
            self.stdout.write("pengawas already exists, skipping.")

        # --- 3 Paslon ---
        paslon_data = [
            {
                "name": "Paslon Harapan Bangsa",
                "visi": "Mewujudkan masyarakat yang sejahtera, adil, dan makmur melalui pembangunan berkelanjutan yang berpusat pada rakyat. Kami percaya bahwa kemajuan sejati tercapai ketika setiap warga mendapat akses yang setara terhadap pendidikan berkualitas, layanan kesehatan terjangkau, dan peluang ekonomi yang merata di seluruh penjuru negeri.",
                "misi": "1. Meningkatkan kualitas pendidikan dengan merevitalisasi kurikulum dan meningkatkan kesejahteraan guru.\n2. Membangun infrastruktur kesehatan yang merata dari kota hingga desa.\n3. Mendorong ekonomi digital dan kewirausahaan masyarakat.\n4. Memperkuat transparansi dan akuntabilitas pemerintahan melalui teknologi.\n5. Melestarikan lingkungan melalui kebijakan pembangunan hijau.",
                "members": [
                    {"name": "Budi Santoso", "role": "Calon Bupati"},
                    {"name": "Ahmad Yani", "role": "Wakil Calon Bupati"},
                ],
            },
            {
                "name": "Paslon Maju Bersama",
                "visi": "Membangun daerah yang inovatif, inklusif, dan kompetitif dengan mengedepankan good governance dan pemberdayaan masyarakat. Visi kami adalah menjadikan daerah sebagai pusat inovasi yang memberdayakan seluruh lapisan masyarakat tanpa terkecuali.",
                "misi": "1. Mengembangkan smart city untuk efisiensi layanan publik.\n2. Meningkatkan partisipasi masyarakat dalam perencanaan pembangunan.\n3. Membangun kawasan ekonomi kreatif dan pariwisata berkelanjutan.\n4. Menjamin keadilan sosial melalui program perlindungan sosial komprehensif.\n5. Meningkatkan konektivitas daerah melalui infrastruktur transportasi modern.",
                "members": [
                    {"name": "Siti Rahmawati", "role": "Calon Bupati"},
                    {"name": "Dewi Lestari", "role": "Wakil Calon Bupati"},
                ],
            },
            {
                "name": "Paslon Untuk Rakyat",
                "visi": "Mewujudkan pemerintahan yang bersih, peduli, dan pro-rakyat melalui reformasi birokrasi dan pemerataan pembangunan. Kami berkomitmen untuk mengabdi sepenuh hati bagi kemajuan daerah dan kesejahteraan seluruh rakyat tanpa diskriminasi.",
                "misi": "1. Reformasi birokrasi menuju pelayanan publik yang cepat dan transparan.\n2. Pemberdayaan UMKM dan pertanian modern untuk kemandirian ekonomi.\n3. Pembangunan infrastruktur dasar yang merata: jalan, air bersih, listrik.\n4. Peningkatan kualitas SDM melalui beasiswa dan pelatihan kerja.\n5. Penguatan institusi anti-korupsi di tingkat daerah.",
                "members": [
                    {"name": "Rizky Pratama", "role": "Calon Bupati"},
                    {"name": "Nurul Hidayah", "role": "Wakil Calon Bupati"},
                ],
            },
        ]

        photo_path = "candidates/photos/745x489-img-69258-potret-ragil-mahardika-instagramragilmahardika.jpg"

        for i, data in enumerate(paslon_data):
            if not User.objects.filter(username=f"paslon{i+1}").exists():
                paslon_user = User.objects.create_user(
                    username=f"paslon{i+1}",
                    email=f"paslon{i+1}@evote.id",
                    password=DEMO_PASSWORD,
                    first_name=f"Paslon",
                    last_name=f"{i+1}",
                    role="paslon",
                )
            else:
                paslon_user = User.objects.get(username=f"paslon{i+1}")

            if not Candidate.objects.filter(user=paslon_user).exists():
                candidate = Candidate.objects.create(
                    user=paslon_user,
                    candidate_number=i + 1,
                    name=data["name"],
                    visi=data["visi"],
                    misi=data["misi"],
                    photo=photo_path,
                    status="approved",
                    verified_by=User.objects.get(username="pengawas"),
                )
                for member in data["members"]:
                    CandidateMember.objects.create(
                        candidate=candidate,
                        name=member["name"],
                        role=member["role"],
                    )
                self.stdout.write(self.style.SUCCESS(f"Created {data['name']}"))
            else:
                self.stdout.write(f"{data['name']} already exists, skipping.")

        # --- Pemilih ---
        faculties = ["Fakultas Teknik", "Fakultas Ilmu Komputer", "Fakultas Ekonomi", "Fakultas Hukum", "Fakultas MIPA"]
        programs = ["Informatika", "Sistem Informasi", "Teknik Sipil", "Manajemen", "Ilmu Hukum", "Matematika"]
        first_names = ["Ahmad", "Budi", "Citra", "Dian", "Eka", "Fajar", "Gita", "Hana", "Indra", "Joko",
                       "Kartika", "Lina", "Maya", "Nadia", "Omar", "Putri", "Qori", "Rina", "Sari", "Tono",
                       "Umi", "Vina", "Wulan", "Yanti", "Zahra"]
        last_names = ["Pratama", "Saputra", "Wijaya", "Kusuma", "Hidayat", "Nugraha", "Ramadhan", "Permana", "Setiawan", "Anggraeni"]

        candidates = list(Candidate.objects.filter(status="approved"))
        pengawas = User.objects.get(username="pengawas")
        voted_count = 0

        for n in range(1, total_voters + 1):
            username = f"pemilih{n}"
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            nik = f"32{random.randint(10,15)}{random.randint(100000000000, 999999999999)}"
            npm = f"{random.choice([20,21,22,23])}{random.randint(1000000, 9999999)}"

            if User.objects.filter(username=username).exists():
                continue

            user = User.objects.create_user(
                username=username,
                email=f"{username}@evote.id",
                password=DEMO_PASSWORD,
                first_name=fname,
                last_name=lname,
                role="pemilih",
            )

            Voter.objects.create(
                user=user,
                nik=nik,
                npm=npm,
                email=user.email,
                full_name=f"{fname} {lname}",
                faculty=random.choice(faculties),
                study_program=random.choice(programs),
                status="active",
            )

            if n <= int(total_voters * vote_fraction) and candidates:
                candidate = random.choice(candidates)
                Vote.objects.create(voter=user, candidate=candidate)
                Voter.objects.filter(user=user).update(has_voted=True)
                voted_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created {total_voters} voters ({voted_count} already voted)"
        ))
        self.stdout.write(self.style.SUCCESS("Seed complete."))
