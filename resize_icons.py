import os

from PIL import Image

# ── Paths ───────────────────────────────────────────────────────────────────
MASTER_LOGO = r"c:\Users\abhin\.gemini\antigravity\brain\a14c5a4b-bd99-469b-bb1c-ef92b38d38a9\bridgeback_logo_master_1776260913858.png"
RES_DIR = "mobile_app/android/app/src/main/res"

# Android Launcher Icon Sizes (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi)
SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}


def resize_icons():
    if not os.path.exists(MASTER_LOGO):
        print(f"Error: Master logo not found at {MASTER_LOGO}")
        return

    img = Image.open(MASTER_LOGO)

    # Ensure transparency or clean background
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(
            img, mask=img.split()[3] if img.mode == "RGBA" else img.split()[1]
        )
        img = background

    for folder, size in SIZES.items():
        target_path = os.path.join(RES_DIR, folder, "ic_launcher.png")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Resize with high quality
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(target_path, "PNG")
        print(f"Done: {target_path} ({size}x{size})")


if __name__ == "__main__":
    resize_icons()
