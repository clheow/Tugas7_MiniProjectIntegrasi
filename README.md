# Tugas 7 - Mini Project Integrasi OCR dan Deteksi Tanda Tangan

## Cara Menjalankan Program

### 1. Buka folder proyek

Buka folder `Tugas7_MiniProjectIntegrasi` menggunakan Visual Studio Code, kemudian buka terminal pada folder tersebut.

### 2. Instal library Python

Jalankan perintah berikut pada terminal:

```bash
pip install -r requirements.txt
```

Perintah tersebut akan menginstal seluruh library Python yang diperlukan oleh program.

### 3. Instal Tesseract OCR

Instal Tesseract OCR terlebih dahulu jika belum tersedia. Setelah instalasi, pastikan lokasi file `tesseract.exe` sesuai dengan konfigurasi pada `main.py`.

Konfigurasi yang digunakan:

```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Jika Tesseract terinstal di lokasi lain, sesuaikan alamat tersebut dengan lokasi instalasi pada perangkat.

### 4. Jalankan program

Pada terminal Visual Studio Code, jalankan:

```bash
python main.py
```

### 5. Masukkan path gambar ijazah

Setelah program meminta path gambar, masukkan lokasi gambar yang ingin diuji.

Contoh:

```text
Masukkan path gambar ijazah: images/ijazah_001.jpg
```

Tekan **Enter** untuk memulai pemrosesan gambar.

Program akan melakukan crop otomatis pada area nomor ijazah dan tanda tangan berdasarkan koordinat yang telah ditentukan di `main.py`. Karena menggunakan koordinat relatif, tata letak gambar ijazah harus sesuai dengan area yang dikonfigurasi.

### 6. Lihat hasil pemrosesan

Setelah program selesai, hasil akan disimpan pada folder `hasil_integrasi`, meliputi:

* Citra hasil crop nomor ijazah.
* Citra hasil crop tanda tangan.
* Citra hasil enhancement untuk setiap metode.
* Citra hasil thresholding.
* File CSV hasil OCR dan perhitungan CER.
* File CSV hasil verifikasi nomor ijazah dan tanda tangan.

Hasil juga ditampilkan langsung pada terminal, termasuk nomor ijazah yang terbaca, metode dengan CER terendah, nilai CER, status tanda tangan, dan rasio piksel tinta.

## Teknologi dan Library

* Python
* OpenCV
* Tesseract OCR
* Pytesseract
* NumPy
* Pandas

## Struktur Folder

```text
Tugas7_MiniProjectIntegrasi/
├── images/
│   ├── ijazah_001.jpg
│   ├── ijazah_002.jpg
│   ├── ...
│   ├── ijazah_no_TTD_001.jpeg
│   └── ...
├── main.py
├── requirements.txt
└── hasil_integrasi/
```

Folder `hasil_integrasi` dibuat secara otomatis ketika program dijalankan. Folder tersebut menyimpan hasil crop, citra enhancement, citra thresholding, dan file CSV hasil pengujian.

## Persyaratan

Pastikan perangkat sudah memiliki:

1. Python yang telah terinstal.
2. Tesseract OCR yang telah terinstal.
3. Library Python yang tercantum pada `requirements.txt`.

## Catatan

* Pastikan path dan nama file gambar yang dimasukkan benar.
* Nilai koordinat crop dapat disesuaikan pada bagian `NUMBER_BOX` dan `SIGNATURE_BOX` di `main.py` apabila tata letak gambar berbeda.
* Hasil deteksi tanda tangan bergantung pada kualitas gambar, area crop, dan ambang klasifikasi yang digunakan.
* Nilai CER yang lebih rendah menunjukkan hasil OCR yang lebih mendekati nomor ijazah acuan.
