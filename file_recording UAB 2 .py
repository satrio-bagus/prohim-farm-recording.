import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Konfigurasi Halaman & Judul Aplikasi
st.set_page_config(page_title="PROHIM FARM - Recording Broiler", layout="wide")
st.title("🐔 PROHIM FARM - Aplikasi Recording Broiler Digital")

# 2. Panel Input Data Utama Kandang (Sidebar)
st.sidebar.header("📋 Data Awal Kandang")
lokasi = st.sidebar.text_input("Nama Kandang / Lokasi", "PLAYEN, GKD")
tgl_chick_in = st.sidebar.date_input("Tanggal Chick In", datetime(2026, 10, 5))
pop_awal = st.sidebar.number_input("Jumlah Awal Ayam (Ekor)", min_value=1, value=17000, step=100)
bb_doc = st.sidebar.number_input("BB Awal / DOC (gram)", min_value=1, value=42)
jenis_doc = st.sidebar.text_input("Jenis DOC / Grade", "UAB VAK")

# 3. Inisialisasi Database 42 Hari di Memori Aplikasi
if 'df_recording' not in st.session_state:
    hari_list = list(range(1, 43))
    
    # Membuat template dataframe kosong untuk di-input user
    init_data = {
        "Umur (Hari)": hari_list,
        "Mati (Ekor)": [0] * 42,
        "Pakan ACT (Sak)": [0.0] * 42,
        "Pakan Kirim (Sak)": [0.0] * 42,
        "Bobot Sampel ACT (Gr)": [0.0] * 42,
    }
    st.session_state.df_recording = pd.DataFrame(init_data)

st.subheader("📊 Lembar Pencatatan Harian (42 Hari Siklus)")
st.info("💡 Klik dua kali pada sel tabel di bawah untuk mengisi data Mati, Pakan, atau Bobot Sampel.")

# 4. Fitur Tabel Input Interaktif (Data Editor)
edited_df = st.data_editor(
    st.session_state.df_recording,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "Umur (Hari)": st.column_config.NumberColumn(disabled=True),
        "Mati (Ekor)": st.column_config.NumberColumn(min_value=0, default=0),
        "Pakan ACT (Sak)": st.column_config.NumberColumn(min_value=0.0, default=0.0),
        "Pakan Kirim (Sak)": st.column_config.NumberColumn(min_value=0.0, default=0.0),
        "Bobot Sampel ACT (Gr)": st.column_config.NumberColumn(min_value=0.0, default=0.0),
    },
    use_container_width=True
)

# Simpan perubahan input ke session state
st.session_state.df_recording = edited_df

# 5. Logika & Rumus Otomatisasi (Matematika Aplikasi)
df_kalkulasi = edited_df.copy()

# A. Generate Tanggal Otomatis
tanggal_list = [(tgl_chick_in + timedelta(days=int(i))).strftime("%d-%b") for i in range(42)]
df_kalkulasi.insert(0, "Tanggal", tanggal_list)

# B. Hitung Sisa Ayam Otomatis (Deplesi)
sisa_ayam = []
current_pop = pop_awal
for mati in df_kalkulasi["Mati (Ekor)"]:
    current_pop -= mati
    sisa_ayam.append(current_pop)
df_kalkulasi.insert(3, "Sisa Ayam (Ekor)", sisa_ayam)

# C. Hitung Mutasi Stok Gudang Pakan
stok_gudang = []
current_stok = 0.0
for kirim, pakai in zip(df_kalkulasi["Pakan Kirim (Sak)"], df_kalkulasi["Pakan ACT (Sak)"]):
    current_stok += (kirim - pakai)
    stok_gudang.append(current_stok)
df_kalkulasi["Stok Gudang (Sak)"] = stok_gudang

# D. Hitung FCR Kumulatif Otomatis (Asumsi 1 Sak = 50 Kg)
fcr_list = []
total_pakan_kg = 0.0
for i, row in df_kalkulasi.iterrows():
    total_pakan_kg += (row["Pakan ACT (Sak)"] * 50)
    bobot_gr = row["Bobot Sampel ACT (Gr)"]
    sisa_ekor = row["Sisa Ayam (Ekor)"]
    
    if bobot_gr > 0 and sisa_ekor > 0:
        total_bobot_kg = (sisa_ekor * bobot_gr) / 1000
        fcr = total_pakan_kg / total_bobot_kg
        fcr_list.append(round(fcr, 3))
    else:
        fcr_list.append("-")
df_kalkulasi.insert(7, "FCR Kumulatif", fcr_list)

# 6. Menampilkan Hasil Output Tabel Akhir yang Sudah Diolah Otomatis
st.subheader("📋 Hasil Perhitungan Kemitraan Otomatis")
st.dataframe(df_kalkulasi, hide_index=True, use_container_width=True)

# 7. Fitur Simpan & Cetak Data Ke Excel (.xlsx)
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Aksi Database")

# Tombol Download Excel
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv_data = convert_df(df_kalkulasi)
st.sidebar.download_button(
    label="📊 Ekspor Data ke Excel (CSV)",
    data=csv_data,
    file_name=f'Recording_{lokasi}_{datetime.now().strftime("%Y%m%d")}.csv',
    mime='text/csv',
)

if st.sidebar.button("🔄 Reset Siklus Baru", type="primary"):
    del st.session_state.df_recording
    st.rerun()
