
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

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


def _normalize_date(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", value or "")
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
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
        image = ImageOps.exif_transpose(Image.open(path))
        text = pytesseract.image_to_string(image, lang="eng+kor")
        return _clean_text(text)
    except Exception:
        return ""


def _extract_from_mrz(text: str) -> dict[str, str]:
    lines = [re.sub(r"\s+", "", line).upper() for line in text.splitlines() if "<" in line]
    lines = [line for line in lines if len(line) >= 30]
    if len(lines) < 2:
        return {}
    line1, line2 = lines[-2], lines[-1]
    data: dict[str, str] = {}
    if line1.startswith("P<"):
        body = line1[2:]
        nationality = body[:3]
        names = body[3:].split("<<", 1)
        surname = names[0].replace("<", " ").strip()
        given = names[1].replace("<", " ").strip() if len(names) > 1 else ""
        full_name = " ".join(part for part in [given, surname] if part).strip()
        data["english_name"] = full_name
        data["name"] = full_name
        data["nationality"] = NATIONALITY_MAP.get(nationality, nationality)
    if len(line2) >= 27:
        data["document_number"] = line2[:9].replace("<", "").strip()
        data["birth_date"] = _parse_mrz_date(line2[13:19])
        gender = line2[20:21].replace("<", "").strip()
        if gender == "M":
            data["gender"] = "남"
        elif gender == "F":
            data["gender"] = "여"
        nationality = line2[10:13].replace("<", "").strip()
        if nationality and not data.get("nationality"):
            data["nationality"] = NATIONALITY_MAP.get(nationality, nationality)
    return data


def _extract_generic(text: str, document_type: str) -> dict[str, str]:
    upper_text = text.upper()
    data: dict[str, str] = {}

    for pattern in [
        r"Name[:\s]+([A-Z][A-Z\s]{2,40})",
        r"Surname[:\s]+([A-Z][A-Z\s]{2,40})",
    ]:
        match = re.search(pattern, upper_text)
        if match and not data.get("english_name"):
            data["english_name"] = re.sub(r"\s+", " ", match.group(1)).strip()
            data["name"] = data["english_name"]

    nationality_match = re.search(r"Nationality[:\s]+([A-Z]{3,20})", upper_text)
    if nationality_match:
        code = nationality_match.group(1).strip()
        data["nationality"] = NATIONALITY_MAP.get(code, code)

    if document_type == "passport":
        number_match = re.search(r"(Passport\s*No|Document\s*No)[:\s]*([A-Z0-9]{6,12})", text, re.I)
    else:
        number_match = re.search(r"(ID\s*No|Card\s*No|Number)[:\s]*([A-Z0-9\-]{6,20})", text, re.I)
    if number_match:
        data["document_number"] = number_match.group(2).strip()

    birth_match = re.search(r"(Date\s*of\s*Birth|Birth)[:\s]*([0-9./\-]{6,12})", text, re.I)
    if birth_match:
        data["birth_date"] = _normalize_date(birth_match.group(2))

    gender_match = re.search(r"(Sex|Gender)[:\s]*(M|F|Male|Female|남|여)", text, re.I)
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
    generic_data = _extract_generic(text, document_type)
    merged: dict[str, Any] = {**generic_data, **mrz_data}
    if selected_country and not merged.get("nationality"):
        merged["nationality"] = COUNTRY_HINT_TO_NATIONALITY.get(selected_country, "")
    photo_path = ""
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        photo_path = _save_cropped_photo(file_path, employee_id, document_type, upload_root)

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
