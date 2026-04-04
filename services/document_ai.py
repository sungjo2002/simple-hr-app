
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import pytesseract
except Exception:
    pytesseract = None


@dataclass
class ExtractionResult:
    text: str = ""
    name: str = ""
    english_name: str = ""
    local_name: str = ""
    nationality: str = ""
    document_number: str = ""
    birth_date: str = ""
    gender: str = ""
    photo_path: str = ""
    status: str = "stored"


NATIONALITY_MAP = {
    "KOR": "대한민국",
    "VNM": "베트남",
    "UZB": "우즈베키스탄",
    "THA": "태국",
    "NPL": "네팔",
    "IDN": "인도네시아",
    "MMR": "미얀마",
    "PHL": "필리핀",
    "KGZ": "키르기스스탄",
    "MNG": "몽골",
    "CHN": "중국",
    "RUS": "러시아",
    "PAK": "파키스탄",
    "LAO": "라오스",
    "KHM": "캄보디아",
    "LKA": "스리랑카",
    "BGD": "방글라데시",
    "TLS": "동티모르",
    "TJK": "타지키스탄",
}

COUNTRY_HINT_TO_NATIONALITY = {
    "vietnam": "베트남",
    "philippines": "필리핀",
    "thailand": "태국",
    "indonesia": "인도네시아",
    "mongolia": "몽골",
    "sri_lanka": "스리랑카",
    "cambodia": "캄보디아",
    "uzbekistan": "우즈베키스탄",
    "pakistan": "파키스탄",
    "myanmar": "미얀마",
    "nepal": "네팔",
    "bangladesh": "방글라데시",
    "kyrgyzstan": "키르기스스탄",
    "timor_leste": "동티모르",
    "laos": "라오스",
    "china": "중국",
    "tajikistan": "타지키스탄",
}


def _clean_text(value: str) -> str:
    return re.sub(r"[\u0000-\u001f]+", " ", value or "").strip()


def _ascii_upper(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).upper()


def _normalize_date(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", value or "")
    if len(digits) == 8:
        if digits[:4].startswith(("19", "20")):
            return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
        return f"20{digits[:2]}-{digits[2:4]}-{digits[4:6]}"
    if len(digits) == 6:
        return _parse_mrz_date(digits)
    return value.strip()


def _parse_mrz_date(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", value or "")
    if len(digits) != 6:
        return ""
    year = int(digits[:2])
    month = digits[2:4]
    day = digits[4:6]
    prefix = "20" if year < 40 else "19"
    return f"{prefix}{digits[:2]}-{month}-{day}"


def _ocr_image(path: str) -> str:
    if pytesseract is None:
        return ""
    try:
        original = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    except Exception:
        return ""

    images = [original]
    gray = ImageOps.grayscale(original)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = gray.filter(ImageFilter.SHARPEN)
    images.append(gray)
    bw = gray.point(lambda px: 255 if px > 150 else 0)
    images.append(bw)

    chunks: list[str] = []
    for img, cfg in [
        (images[0], "--psm 6"),
        (images[1], "--psm 6"),
        (images[1], "--psm 11"),
        (images[2], "--psm 6"),
    ]:
        try:
            chunks.append(pytesseract.image_to_string(img, lang="eng+kor", config=cfg, timeout=15))
        except Exception:
            continue
    return _clean_text("\n".join(part for part in chunks if part))


def _mrz_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        candidate = _ascii_upper(raw).replace("«", "<")
        candidate = re.sub(r"[^A-Z0-9<]", "", candidate)
        if len(candidate) >= 24 and ("<" in candidate or candidate.startswith("P")):
            lines.append(candidate)
    return lines


def _extract_from_mrz(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    lines = _mrz_lines(text)

    for idx in range(max(0, len(lines) - 1)):
        line1 = lines[idx].replace("PSVNM", "P<VNM").replace("PVNM", "P<VNM")
        line2 = lines[idx + 1].replace(" ", "")
        if not (line1.startswith("P<") or "VNM" in line1[:10]):
            continue

        name_match = re.search(r"P<?([A-Z]{3})([A-Z<]{4,44})", line1)
        if name_match:
            nat = name_match.group(1)
            blob = name_match.group(2)
            if "<<" in blob:
                surname, given = blob.split("<<", 1)
            else:
                parts = blob.split("<", 1)
                surname = parts[0]
                given = parts[1] if len(parts) > 1 else ""
            full_name = " ".join(
                part for part in [given.replace("<", " ").strip(), surname.replace("<", " ").strip()] if part
            ).strip()
            if full_name:
                data["english_name"] = re.sub(r"\s+", " ", full_name)
                data["name"] = data["english_name"]
            data["nationality"] = NATIONALITY_MAP.get(nat, nat)

        line2_match = re.search(r"([A-Z]\d{7,8})<?\d?<*([A-Z]{3})(\d{6}).([MF<])(\d{6})", line2)
        if line2_match:
            data["document_number"] = line2_match.group(1)
            data.setdefault("nationality", NATIONALITY_MAP.get(line2_match.group(2), line2_match.group(2)))
            data["birth_date"] = _parse_mrz_date(line2_match.group(3))
            sex = line2_match.group(4)
            if sex == "M":
                data["gender"] = "남"
            elif sex == "F":
                data["gender"] = "여"
        if data:
            return data

    joined = re.sub(r"[^A-Z0-9<]", "", _ascii_upper(text))
    joined = joined.replace("PSVNM", "P<VNM").replace("PVNM", "P<VNM")
    line2_match = re.search(r"([A-Z]\d{7,8})<?\d?<*([A-Z]{3})(\d{6}).([MF<])(\d{6})", joined)
    if line2_match:
        data["document_number"] = line2_match.group(1)
        data["birth_date"] = _parse_mrz_date(line2_match.group(3))
        data["nationality"] = NATIONALITY_MAP.get(line2_match.group(2), line2_match.group(2))
        sex = line2_match.group(4)
        if sex == "M":
            data["gender"] = "남"
        elif sex == "F":
            data["gender"] = "여"
    return data


def _extract_vietnam_passport(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    normalized = _ascii_upper(text)
    normalized = re.sub(r"\s+", " ", normalized)

    for pattern in [
        r"FULL NAME\s+([A-Z ]{4,60}?)\s+(?:QUE|QUOC|NATIONALITY|NGAY|DATE OF BIRTH|SEX)",
        r"HO VA TEN\s*/?\s*FULL NAME\s+([A-Z ]{4,60}?)\s+(?:QUE|QUOC|NATIONALITY|NGAY|DATE OF BIRTH|SEX)",
        r"FULL NAME\s+([A-Z ]{4,60}?)\s+VIET NAM",
    ]:
        match = re.search(pattern, normalized)
        if match:
            name = re.sub(r"\s+", " ", match.group(1)).strip(" -_/")
            if len(name.split()) >= 2:
                data["english_name"] = name
                data["name"] = name
                break

    for pattern in [
        r"PASSPORT\s*N\S*\s*([A-Z]\d{7,8})",
        r"SO HO CHIEU\s*/?\s*PASSPORT\s*N\S*\s*([A-Z]\d{7,8})",
        r"\b([A-Z]\d{7,8})\b",
    ]:
        match = re.search(pattern, normalized)
        if match:
            data["document_number"] = match.group(1).replace(" ", "")
            break

    birth_match = re.search(r"DATE OF BIRTH[^0-9]{0,20}(\d{2})\s*[/.-]\s*(\d{2})\s*[/.-]\s*(\d{4})", normalized)
    if birth_match:
        dd, mm, yyyy = birth_match.group(1), birth_match.group(2), birth_match.group(3)
        data["birth_date"] = f"{yyyy}-{mm}-{dd}"

    sex_match = re.search(r"(?:SEX|GIOI TINH)[^A-Z0-9]{0,20}(NAM/?M|NU/?F|MALE|FEMALE|M|F)", normalized)
    if sex_match:
        raw = sex_match.group(1)
        if "NAM" in raw or raw == "M" or "MALE" in raw:
            data["gender"] = "남"
        elif "NU" in raw or raw == "F" or "FEMALE" in raw:
            data["gender"] = "여"

    if "VIET NAMESE" in normalized or "VIET NAM / VIETNAMESE" in normalized or "NATIONALITY VIET NAM" in normalized:
        data["nationality"] = "베트남"

    return data


def _extract_generic(text: str, document_type: str) -> dict[str, str]:
    upper_text = _ascii_upper(text)
    data: dict[str, str] = {}

    for pattern in [
        r"NAME[:\s]+([A-Z][A-Z\s]{2,40})",
        r"SURNAME[:\s]+([A-Z][A-Z\s]{2,40})",
    ]:
        match = re.search(pattern, upper_text)
        if match and not data.get("english_name"):
            data["english_name"] = re.sub(r"\s+", " ", match.group(1)).strip()
            data["name"] = data["english_name"]

    nationality_match = re.search(r"NATIONALITY[:\s/]+([A-Z]{3,20})", upper_text)
    if nationality_match:
        code = nationality_match.group(1).strip()
        data["nationality"] = NATIONALITY_MAP.get(code, code)

    if document_type == "passport":
        number_match = re.search(r"(PASSPORT\s*NO|DOCUMENT\s*NO|PASSPORT\s*N)[:\s°]*([A-Z0-9]{6,12})", upper_text)
    else:
        number_match = re.search(r"(ID\s*NO|CARD\s*NO|NUMBER)[:\s]*([A-Z0-9\-]{6,20})", upper_text)
    if number_match:
        data["document_number"] = number_match.group(2).strip()

    birth_match = re.search(r"(DATE\s*OF\s*BIRTH|BIRTH)[:\s]*([0-9./\-]{6,12})", upper_text)
    if birth_match:
        data["birth_date"] = _normalize_date(birth_match.group(2))

    gender_match = re.search(r"(SEX|GENDER)[:\s]*(M|F|MALE|FEMALE|남|여)", upper_text)
    if gender_match:
        raw = gender_match.group(2).strip().lower()
        data["gender"] = "남" if raw in {"m", "male", "남"} else "여"

    return data


def _save_cropped_photo(image_path: str, employee_id: int, document_type: str, upload_root: str) -> str:
    try:
        image = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
    except Exception:
        return ""
    width, height = image.size
    if width < 200 or height < 200:
        return ""
    if document_type == "passport":
        crop = (int(width * 0.06), int(height * 0.42), int(width * 0.34), int(height * 0.90))
    elif document_type == "id_card":
        crop = (int(width * 0.60), int(height * 0.08), int(width * 0.96), int(height * 0.88))
    else:
        crop = (int(width * 0.10), int(height * 0.10), int(width * 0.40), int(height * 0.90))
    cropped = image.crop(crop)
    cropped = ImageOps.fit(cropped, (420, 560), method=Image.Resampling.LANCZOS)
    profile_dir = Path(upload_root) / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    output_path = profile_dir / f"employee_{employee_id}_{document_type}_photo.jpg"
    cropped.save(output_path, format="JPEG", quality=92)
    return f"/uploads/profiles/{output_path.name}"


def extract_document_data(*, file_path: str, employee_id: int, document_type: str, upload_root: str, selected_country: str = "") -> ExtractionResult:
    suffix = Path(file_path).suffix.lower()
    text = ""
    status = "stored"
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        text = _ocr_image(file_path)
        if text:
            status = "ocr_success"
        elif pytesseract is None:
            status = "ocr_unavailable"
        else:
            status = "ocr_empty"
    elif suffix == ".pdf":
        status = "pdf_stored_only"

    mrz_data = _extract_from_mrz(text)
    country_data = _extract_vietnam_passport(text) if document_type == "passport" and selected_country == "vietnam" else {}
    generic_data = _extract_generic(text, document_type)

    merged: dict[str, str] = {}
    for source in (generic_data, country_data, mrz_data):
        for key, value in source.items():
            if value:
                merged[key] = value

    if selected_country and not merged.get("nationality"):
        merged["nationality"] = COUNTRY_HINT_TO_NATIONALITY.get(selected_country, "")

    photo_path = ""
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        photo_path = _save_cropped_photo(file_path, employee_id, document_type, upload_root)

    filled = sum(1 for key in ("name", "english_name", "nationality", "document_number", "birth_date", "gender") if merged.get(key))
    if status == "ocr_success" and filled <= 1:
        status = "ocr_empty"

    return ExtractionResult(
        text=text[:10000],
        name=_clean_text(merged.get("name", "")),
        english_name=_clean_text(merged.get("english_name", "")),
        local_name=_clean_text(merged.get("local_name", "")),
        nationality=_clean_text(merged.get("nationality", "")),
        document_number=_clean_text(merged.get("document_number", "")),
        birth_date=_clean_text(merged.get("birth_date", "")),
        gender=_clean_text(merged.get("gender", "")),
        photo_path=photo_path,
        status=status,
    )
