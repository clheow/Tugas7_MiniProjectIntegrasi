
import argparse
import os
import re
import cv2
import numpy as np
import pandas as pd
import pytesseract

# =========================================================
# KONFIGURASI
# =========================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
GROUND_TRUTH = "NOMORIJAZAH571012022000056"
OUTPUT_DIR = "hasil_integrasi"

METHOD_FOLDER = {
    "Original": "original",
    "Mean Filter": "mean_filter",
    "Median Filter": "median_filter",
    "Gaussian Filter": "gaussian_filter",
    "Sharpening": "sharpening",
}


# Sesuaikan berdasarkan contoh gambar ijazah yang digunakan.
NUMBER_BOX = (0.05, 0.88, 0.40, 0.98)
SIGNATURE_BOX = (0.14, 0.70, 0.40, 0.82)


SIGNATURE_THRESHOLD = 0.03


def normalize_text(text):
    """Mengubah teks menjadi huruf besar tanpa spasi/tanda baca."""
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def levenshtein_distance(reference, hypothesis):
    """Menghitung jarak edit antara dua teks."""
    rows = len(reference) + 1
    cols = len(hypothesis) + 1
    dp = [[0] * cols for _ in range(rows)]

    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )

    return dp[-1][-1]


def calculate_cer(reference, hypothesis):
    """Menghitung Character Error Rate dalam persen."""
    reference = normalize_text(reference)
    hypothesis = normalize_text(hypothesis)

    if not reference:
        return 0.0 if not hypothesis else 100.0

    return (
        levenshtein_distance(reference, hypothesis)
        / len(reference) * 100.0
    )


def automatic_crop(image, box):
    """
    Memotong area otomatis berdasarkan koordinat relatif gambar.
    box = (x_awal, y_awal, x_akhir, y_akhir).
    """
    height, width = image.shape[:2]
    x1, y1, x2, y2 = box

    x1 = max(0, min(int(x1 * width), width - 1))
    y1 = max(0, min(int(y1 * height), height - 1))
    x2 = max(x1 + 1, min(int(x2 * width), width))
    y2 = max(y1 + 1, min(int(y2 * height), height))

    return image[y1:y2, x1:x2].copy()


def enhance_number_area(gray):
    """Menerapkan lima metode enhancement."""
    mean_filter = cv2.blur(gray, (5, 5))
    median_filter = cv2.medianBlur(gray, 5)
    gaussian_filter = cv2.GaussianBlur(gray, (5, 5), 0)

    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ], dtype=np.float32)

    sharpening = cv2.filter2D(gray, -1, kernel)

    return {
        "Original": gray.copy(),
        "Mean Filter": mean_filter,
        "Median Filter": median_filter,
        "Gaussian Filter": gaussian_filter,
        "Sharpening": sharpening,
    }


def prepare_for_ocr(gray_image):
    """Memperbesar gambar dan menerapkan thresholding Otsu."""
    enlarged = cv2.resize(
        gray_image,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    _, binary = cv2.threshold(
        enlarged,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binary



def detect_signature(signature_bgr):
    """
    Deteksi tanda tangan menggunakan thresholding adaptif
    dan analisis komponen terhubung.
    """
    gray = cv2.cvtColor(signature_bgr, cv2.COLOR_BGR2GRAY)

    # Kurangi pola dan noise kecil pada latar belakang.
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Pisahkan goresan gelap dari latar belakang.
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        15
    )

    # Hapus titik-titik kecil.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (3, 3)
    )
    cleaned = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, kernel
    )

    # Hitung komponen yang cukup besar untuk diperiksa.
    jumlah, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(cleaned, 8)
    )

    luas_minimum = 20
    komponen_besar = 0
    total_piksel = 0

    for i in range(1, jumlah):
        luas = stats[i, cv2.CC_STAT_AREA]

        if luas >= luas_minimum:
            komponen_besar += 1
            total_piksel += luas

    ink_ratio = total_piksel / cleaned.size

    # Ambang awal; perlu diuji pada gambar bertanda tangan
    # dan gambar tanpa tanda tangan.
    BATAS_RASIO_TINTA = 0.01

    present = ink_ratio >= BATAS_RASIO_TINTA

    return present, ink_ratio, cleaned


def main():
    parser = argparse.ArgumentParser(
        description="Prototype OCR nomor ijazah dan deteksi tanda tangan."
    )

    parser.add_argument(
        "image",
        nargs="?",
        help="Path gambar ijazah, misalnya images/ijazah_001.jpg"
    )

    parser.add_argument(
        "--ground-truth",
        default=GROUND_TRUTH,
        help="Nomor ijazah asli untuk menghitung CER."
    )

    parser.add_argument(
        "--show-crops",
        action="store_true",
        help="Tampilkan hasil crop otomatis untuk diperiksa."
    )

    args = parser.parse_args()

    if os.path.isfile(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    else:
        raise SystemExit(
            "Tesseract tidak ditemukan. Periksa TESSERACT_PATH."
        )

    image_path = args.image
    if not image_path:
        image_path = input(
            "Masukkan path gambar ijazah (contoh: images/ijazah_001.jpg): "
        ).strip().strip('"')

    image = cv2.imread(image_path)

    if image is None:
        raise SystemExit(
            f"Gagal membaca gambar: {image_path}"
        )

    stem = os.path.splitext(os.path.basename(image_path))[0]

    folders = [
        "crop_nomor",
        "crop_tanda_tangan",
        *METHOD_FOLDER.values(),
        "threshold",
    ]

    for folder in folders:
        os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

    # -----------------------------------------------------
    # 1. CROP OTOMATIS
    # -----------------------------------------------------

    number_crop = automatic_crop(image, NUMBER_BOX)
    signature_crop = automatic_crop(image, SIGNATURE_BOX)

    cv2.imwrite(
        os.path.join(OUTPUT_DIR, "crop_nomor", f"{stem}.png"),
        number_crop
    )

    cv2.imwrite(
        os.path.join(
            OUTPUT_DIR, "crop_tanda_tangan", f"{stem}.png"
        ),
        signature_crop
    )

    if args.show_crops:
        cv2.imshow("Crop Nomor Ijazah", number_crop)
        cv2.imshow("Crop Area Tanda Tangan", signature_crop)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # -----------------------------------------------------
    # 2. OCR DAN PERBANDINGAN CER
    # -----------------------------------------------------

    number_gray = cv2.cvtColor(
        number_crop, cv2.COLOR_BGR2GRAY
    )
    methods = enhance_number_area(number_gray)

    results = []
    best_method = None
    best_cer = None
    best_text = ""

    print("\n========== HASIL OCR DAN CER ==========")

    for method, enhanced in methods.items():
        binary = prepare_for_ocr(enhanced)

        raw_text = pytesseract.image_to_string(
            binary,
            config=(
                "--oem 3 --psm 7 "
                "-c tessedit_char_whitelist="
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-"
            )
        )

        ocr_text = normalize_text(raw_text)
        cer = calculate_cer(args.ground_truth, ocr_text)

        cv2.imwrite(
            os.path.join(
                OUTPUT_DIR, METHOD_FOLDER[method], f"{stem}.png"
            ),
            enhanced
        )

        cv2.imwrite(
            os.path.join(
                OUTPUT_DIR, "threshold",
                f"{stem}_{METHOD_FOLDER[method]}.png"
            ),
            binary
        )

        results.append({
            "Gambar": os.path.basename(image_path),
            "Metode": method,
            "Hasil OCR": ocr_text,
            "Ground Truth": normalize_text(args.ground_truth),
            "CER (%)": round(cer, 2),
        })

        if best_cer is None or cer < best_cer:
            best_cer = cer
            best_method = method
            best_text = ocr_text

        print(
            f"{method:15} | OCR: {ocr_text or '(kosong)':30} "
            f"| CER: {cer:.2f}%"
        )

    # -----------------------------------------------------
    # 3. DETEKSI TANDA TANGAN
    # -----------------------------------------------------

    signature_present, ink_ratio, signature_binary = (
        detect_signature(signature_crop)
    )

    cv2.imwrite(
        os.path.join(
            OUTPUT_DIR,
            "crop_tanda_tangan",
            f"{stem}_threshold_morphology.png"
        ),
        signature_binary
    )

    status_signature = (
        "PRESENT" if signature_present else "ABSENT"
    )

    # -----------------------------------------------------
    # 4. SIMPAN HASIL
    # -----------------------------------------------------

    results_csv = os.path.join(
        OUTPUT_DIR, f"{stem}_hasil_ocr_cer.csv"
    )

    pd.DataFrame(results).to_csv(
        results_csv, index=False, encoding="utf-8-sig"
    )

    summary = pd.DataFrame([{
        "Gambar": os.path.basename(image_path),
        "Nomor Ijazah": best_text,
        "Metode CER Terendah": best_method,
        "CER Terendah (%)": round(best_cer, 2),
        "Tanda Tangan": status_signature,
        "Rasio Piksel Tinta (%)": round(ink_ratio * 100, 2),
    }])

    summary_csv = os.path.join(
        OUTPUT_DIR, f"{stem}_hasil_verifikasi.csv"
    )

    summary.to_csv(
        summary_csv, index=False, encoding="utf-8-sig"
    )

    print("\n========== HASIL VERIFIKASI ==========")
    print(f"Input           : {os.path.basename(image_path)}")
    print("Nomor Ijazah    :", next(
        row["Hasil OCR"]
        for row in results
        if row["Metode"] == best_method
    ))
    print("Tanda Tangan    :", status_signature)

    print("\nInformasi Tambahan:")
    print("Metode OCR Terbaik :", best_method)
    print(f"CER Terendah       : {best_cer:.2f}%")
    print(f"Rasio Piksel Tinta : {ink_ratio * 100:.2f}%")

    print("\nFile hasil:")
    print("-", results_csv)
    print("-", summary_csv)
    print("Folder output:", OUTPUT_DIR)


if __name__ == "__main__":
    main()