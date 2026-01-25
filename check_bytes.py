
with open(r"d:\SOS_42\app\services\embeddings.py", "rb") as f:
    lines = f.readlines()
    if len(lines) >= 12:
        print(f"Line 12: {lines[11]}")
    else:
        print("File has fewer than 12 lines")
