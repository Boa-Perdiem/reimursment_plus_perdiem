# utils/aggregate_receipt_totals.py

import re
from decimal import Decimal
from models import db, Receipt


def clean_number(num_str: str) -> Decimal:
    """
    Financial-safe number parsing.

    Handles:
    - 27.30
    - 15,70
    - 44,800
    - 12,904
    - 1,200,500
    - 1,200,500.45
    - 28,749,87 (OCR broken decimal)
    - 78.000
    - Ugx.44,800
    - $27.30
    """

    # Remove everything except digits, comma, dot
    num_str = re.sub(r"[^\d,\.]", "", num_str)

    if not num_str:
        return Decimal("0.00")

    # ------------------------------------------------
    # CASE 1: Both comma and dot
    # ------------------------------------------------
    if "," in num_str and "." in num_str:
        if num_str.rfind(".") > num_str.rfind(","):
            # Dot is decimal, commas are thousands
            num_str = num_str.replace(",", "")
            return Decimal(num_str)
        else:
            # Comma is decimal, dots are thousands
            num_str = num_str.replace(".", "")
            num_str = num_str.replace(",", ".")
            return Decimal(num_str)

    # ------------------------------------------------
    # CASE 2: Only dot
    # ------------------------------------------------
    if "." in num_str:
        parts = num_str.split(".")
        if len(parts[-1]) == 2:
            # Last 2 digits → decimal
            integer_part = "".join(parts[:-1])
            decimal_part = parts[-1]
            return Decimal(f"{integer_part}.{decimal_part}")
        else:
            # Otherwise → treat as thousands
            return Decimal("".join(parts))

    # ------------------------------------------------
    # CASE 3: Only comma
    # ------------------------------------------------
    if "," in num_str:
        parts = num_str.split(",")
        if len(parts[-1]) <= 2:
            integer_part = "".join(parts[:-1])
            decimal_part = parts[-1]
            return Decimal(f"{integer_part}.{decimal_part}")
        else:
            
            return Decimal("".join(parts))

    # ------------------------------------------------
    # CASE 4: Plain integer
    # ------------------------------------------------
    return Decimal(num_str)


def extract_total_from_text(ocr_text: str) -> Decimal:
    """
    Extracts the LAST valid Total line.
    Ignores Subtotal, Units, Additional, Cash, Change.
    """

    if not ocr_text:
        return Decimal("0.00")

    lines = ocr_text.splitlines()
    extracted_totals = []

    for line in lines:
        lower = line.lower()

        if "total" in lower:
            # Skip unwanted lines
            if any(word in lower for word in [
                "subtotal",
                "units",
                "additional",
                "cash",
                "change"
            ]):
                continue

            '''match = re.search(r"([\d,\.]+)", line)
            if match:
                raw_value = match.group(1)
                value = clean_number(raw_value)'''
            matches = re.findall(r"\d+(?:[.,]\d+)*", line)
            if matches:
                raw_value = matches[-1]  # take the LAST number in line
                value = clean_number(raw_value)

                # Debug prints
                print("RAW LINE:", line)
                print("RAW NUMBER:", raw_value)
                print("CLEANED VALUE:", value)

                extracted_totals.append(value)

    if not extracted_totals:
        return Decimal("0.00")

    # Take LAST valid total
    return extracted_totals[-1]


def aggregate_category_totals(request_id: int):
    """
    Aggregate totals PER CATEGORY.
    Sum all receipt totals inside same category.
    Store same category_total in each receipt of that category.
    """

    receipts = Receipt.query.filter_by(request_id=request_id).all()

    if not receipts:
        print(f"No receipts found for request_id={request_id}")
        return

    # Group receipts by category
    category_map = {}
    for r in receipts:
        category_map.setdefault(r.category, []).append(r)

    for category, recs in category_map.items():

        print("\n---------------------------------------")
        print(f"Processing category: {category}")

        category_sum = Decimal("0.00")

        for r in recs:
            extracted = extract_total_from_text(r.ocr_text)
            print(f"Receipt ID {r.id} -> Extracted Total = {extracted}")
            category_sum += extracted

        print(f"Category '{category}' FINAL SUM = {category_sum}")

        # Update each receipt in this category
        for r in recs:
            r.category_total = category_sum

    db.session.commit()
    print("\n✅ All category totals committed successfully.")
