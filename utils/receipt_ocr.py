import os
from datetime import datetime
from paddleocr import PaddleOCR

# -------------------------------------------------
# INITIALIZE OCR ONCE
# -------------------------------------------------
ocr_engine = PaddleOCR(
    use_angle_cls=True,
    lang="en",
    show_log=False
)


def run_receipt_ocr(
    receipt_path: str,
    perdiem_code: str,  
    requestor_name: str,
    category: str, 
    category_index: int, 
    output_base_dir: str = "static/generated/receipt_ocr_results"
):
    if not os.path.exists(receipt_path):
        raise FileNotFoundError(f"Receipt not found: {receipt_path}")

    # -------------------------------------------------
    # PER-PERDIEM DIRECTORY
    # -------------------------------------------------
    perdiem_dir = os.path.join(output_base_dir, perdiem_code)
    os.makedirs(perdiem_dir, exist_ok=True)

    # -------------------------------------------------
    # UNIQUE FILE PER RECEIPT (NO OVERWRITE)
    # -------------------------------------------------
    #timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    safe_category = category
    safe_requestor = requestor_name.replace(" ", "_")
    existing = [
        f for f in os.listdir(perdiem_dir)
        if f.startswith(f"receipt_{safe_requestor}_{safe_category}")
        and f.endswith(".txt")
    ]

    index = len(existing) + 1

    if index == 1:
        output_filename = f"receipt_{safe_requestor}_{safe_category}.txt"
    else:
        output_filename = f"receipt_{safe_requestor}_{safe_category}_{index}.txt"

    output_path = os.path.join(perdiem_dir, output_filename)


    #output_filename = f"receipt_{safe_requestor}_{safe_category}.txt"
    #output_filename = f"receipt_{safe_requestor}_{timestamp}.txt"
    output_path = os.path.join(perdiem_dir, output_filename)

    # -------------------------------------------------
    # OCR
    # -------------------------------------------------
    result = ocr_engine.ocr(receipt_path, cls=True)

    boxes = []

    for page in result:
        for line in page:
            box = line[0]
            text = line[1][0]

            x_left = min(p[0] for p in box)
            y_center = sum(p[1] for p in box) / 4

            boxes.append({
                "text": text,
                "x": x_left,
                "y": y_center
            })

    # -------------------------------------------------
    # ROW GROUPING
    # -------------------------------------------------
    ROW_THRESHOLD = 10
    rows = []

    for item in sorted(boxes, key=lambda b: b["y"]):
        placed = False
        for row in rows:
            if abs(row["y"] - item["y"]) <= ROW_THRESHOLD:
                row["items"].append(item)
                placed = True
                break
        if not placed:
            rows.append({
                "y": item["y"],
                "items": [item]
            })

    # -------------------------------------------------
    # SORT + WRITE OUTPUT
    # -------------------------------------------------
    output_lines = []

    for row in rows:
        row_items = sorted(row["items"], key=lambda b: b["x"])
        line_text = " ".join(item["text"] for item in row_items)
        output_lines.append(line_text)

    extracted_text = "\n".join(output_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    return output_path, extracted_text
