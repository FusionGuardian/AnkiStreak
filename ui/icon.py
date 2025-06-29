import os
import base64

ICON_FILENAMES = {
    "streak": "./icons/streakIcon.png",
    "grey_streak": "./icons/greyStreakIcon.png",
    "frozen_streak": "./icons/frozenStreakIcon.png",
    "share": "./icons/shareIcon.png",
    "copy": "./icons/copyIcon.png",
    "download": "./icons/downloadIcon.png",
    "facebook": "./icons/facebookIcon.png",
    "x": "./icons/xIcon.png",
}

def get_base64_icon_data(icon_name: str) -> str:
    filename = ICON_FILENAMES.get(icon_name)
    if not filename:
        raise ValueError(f"Unknown icon name: {icon_name}")

    icon_path = os.path.join(os.path.dirname(__file__), "..", filename)
    with open(icon_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"