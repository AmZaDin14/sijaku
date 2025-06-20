import math
from datetime import datetime, time, timedelta

from .models import MataKuliah

DURASI_PER_SKS = 30  # Ganti sesuai aturan kampus Anda, misal: 50


def get_durasi_menit(matakuliah: MataKuliah, durasi_per_sks: int = DURASI_PER_SKS):
    """Mengubah SKS menjadi durasi dalam menit."""
    return matakuliah.sks * durasi_per_sks


def find_divisors(n: int):
    """Mencari semua faktor pembagi dari sebuah angka n."""
    divs = set()
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divs.add(i)
            divs.add(n // i)
    return sorted(list(divs))


def find_optimal_interval(sks_duration_in_minutes: int):
    """Menentukan interval menit yang paling cocok secara otomatis."""
    if sks_duration_in_minutes <= 0:
        raise ValueError("Durasi SKS harus positif.")
    divisors = find_divisors(sks_duration_in_minutes)
    preferred_intervals = [5, 10, 15]
    for p_interval in preferred_intervals:
        if p_interval in divisors:
            return p_interval

    MAX_REASONABLE_INTERVAL = 15
    reasonable_divisors = [d for d in divisors if 1 < d < sks_duration_in_minutes]
    if not reasonable_divisors:
        return 1

    best_fallback = max(
        [d for d in reasonable_divisors if d <= MAX_REASONABLE_INTERVAL] or [0]
    )
    if best_fallback > 0:
        return best_fallback
    else:
        return min(reasonable_divisors)


def get_time_blocks(start_time: time, end_time: time, interval_menit: int = 10):
    """Memecah rentang waktu menjadi blok-blok kecil."""
    blocks = []
    base_date = datetime.now().date()
    current = datetime.combine(base_date, start_time)
    end = datetime.combine(base_date, end_time)
    while current < end:
        blocks.append(current.time().strftime("%H:%M"))
        current += timedelta(minutes=interval_menit)
    return blocks


def generate_all_possible_slots(jadwal_harian_list, matakuliah_list, interval_menit):
    """Menghasilkan semua kemungkinan slot waktu yang valid."""
    durasi_unik = set(get_durasi_menit(mk) for mk in matakuliah_list)
    all_slots = {}
    for jadwal_harian in jadwal_harian_list:
        hari = jadwal_harian.hari
        all_slots[hari] = {}
        base_date = datetime.now().date()
        jam_mulai = datetime.combine(base_date, jadwal_harian.jam_mulai)
        jam_selesai = datetime.combine(base_date, jadwal_harian.jam_selesai)
        istirahat_mulai = datetime.combine(base_date, jadwal_harian.istirahat_mulai)
        istirahat_selesai = datetime.combine(base_date, jadwal_harian.istirahat_selesai)
        for durasi in durasi_unik:
            key_durasi = f"{durasi}_menit"
            all_slots[hari][key_durasi] = []
            current_time = jam_mulai
            while current_time < jam_selesai:
                slot_mulai = current_time
                slot_selesai = current_time + timedelta(minutes=durasi)
                if slot_selesai > jam_selesai:
                    break
                is_overlapping_break = (
                    slot_mulai < istirahat_selesai and slot_selesai > istirahat_mulai
                )
                if not is_overlapping_break:
                    all_slots[hari][key_durasi].append(
                        (slot_mulai.time(), slot_selesai.time())
                    )
                current_time += timedelta(minutes=interval_menit)
    return all_slots
