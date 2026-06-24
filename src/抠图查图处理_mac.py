#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections.abc import Callable
import ctypes
import json
import os
import subprocess
import shutil
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageTk


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
RETRY_FOLDER_NAME = "等待重新抠图"
DONE_FOLDER_SUFFIX = "（已查图）"
UI_FONT = "Microsoft YaHei UI" if sys.platform == "win32" else "PingFang SC"
WINDOW_TITLE = "查图处理 v9"
APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "抠图查图处理"
CONFIG_PATH = APP_SUPPORT_DIR / "config.json"
PHOTOSHOP_BUNDLE_ID = "com.adobe.Photoshop"
PHOTOSHOP_APP_PATH = Path("/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app")
BG_COLOR_1 = (238, 238, 238, 255)
BG_COLOR_2 = (208, 208, 208, 255)
WHITE_BORDER_SIZE = 2
NEAR_BLACK_THRESHOLD = 64
BOLDEN_SIZE_1 = 1
BOLDEN_SIZE_2 = 2
MAX_UNDO_STEPS = 20
ERASER_DEFAULT_SIZE = 20
ERASER_MIN_SIZE = 2
ERASER_MAX_SIZE = 200
ERASER_SIZE_STEP = 5
ERASER_TRANSPARENT_FORMATS = {"PNG", "WEBP"}

THEME_BG = "#15171d"
THEME_PANEL_BG = "#20242c"
THEME_CANVAS_BG = "#101216"
THEME_TEXT = "#eef2f7"
THEME_MUTED = "#aeb7c4"
THEME_BUTTON_BG = "#2b3039"
THEME_BUTTON_ACTIVE_BG = "#38404c"
MAC_BUTTON_BG = "#f3f4f6"
MAC_BUTTON_ACTIVE_BG = "#e5e7eb"
MAC_BUTTON_TEXT = "#111827"
THEME_ENTRY_BG = "#0f1116"
THEME_ENTRY_BORDER = "#3a424e"
THEME_WARNING = "#ff8f8f"

LIGHT_BACKGROUNDS = {"#f0f0f0", "#f2f2f2", "#f6f6f6", "#ffffff", "white"}
DEFAULT_FOREGROUNDS = {"black", "#000000", "systemwindowtext", "systembuttontext"}


def configure_safe(widget: tk.Misc, **kwargs: object) -> None:
    for key, value in kwargs.items():
        try:
            widget.configure(**{key: value})
        except tk.TclError:
            pass


def normalized_tk_color(value: object) -> str:
    return str(value).strip().lower()


def is_light_or_system_background(value: object) -> bool:
    color = normalized_tk_color(value)
    return color in LIGHT_BACKGROUNDS or color.startswith("system")


def parent_background(widget: tk.Misc, fallback: str = THEME_BG) -> str:
    parent = getattr(widget, "master", None)
    if parent is None:
        return fallback
    try:
        return str(parent.cget("bg"))
    except tk.TclError:
        return fallback


def install_dark_theme(root: tk.Tk) -> None:
    root.configure(bg=THEME_BG)
    root.option_add("*Background", THEME_BG)
    root.option_add("*Foreground", THEME_TEXT)
    root.option_add("*Label.Background", THEME_BG)
    root.option_add("*Label.Foreground", THEME_TEXT)
    if sys.platform == "darwin":
        root.option_add("*Button.Background", MAC_BUTTON_BG)
        root.option_add("*Button.Foreground", MAC_BUTTON_TEXT)
    else:
        root.option_add("*Button.Background", THEME_BUTTON_BG)
        root.option_add("*Button.Foreground", THEME_TEXT)
    root.option_add("*Entry.Background", THEME_ENTRY_BG)
    root.option_add("*Entry.Foreground", THEME_TEXT)
    root.option_add("*Entry.InsertBackground", THEME_TEXT)
    root.option_add("*selectBackground", "#355d90")
    root.option_add("*selectForeground", THEME_TEXT)


def apply_dark_theme(widget: tk.Misc) -> None:
    if isinstance(widget, (tk.Tk, tk.Toplevel)):
        configure_safe(widget, bg=THEME_BG)
    elif isinstance(widget, tk.Canvas):
        configure_safe(widget, bg=THEME_CANVAS_BG, highlightthickness=0)
    elif isinstance(widget, (tk.Frame, tk.LabelFrame)):
        current_bg = normalized_tk_color(widget.cget("bg"))
        bg = THEME_CANVAS_BG if current_bg == "#f0f0f0" else THEME_PANEL_BG if current_bg in {"#f2f2f2", "#f6f6f6"} else THEME_BG
        configure_safe(widget, bg=bg, highlightbackground=THEME_ENTRY_BORDER)
    elif isinstance(widget, tk.Label):
        current_bg = normalized_tk_color(widget.cget("bg"))
        current_fg = normalized_tk_color(widget.cget("fg"))
        bg = THEME_PANEL_BG if current_bg in {"#f2f2f2", "#f6f6f6"} else parent_background(widget)
        if current_fg == "#555555":
            fg = THEME_MUTED
        elif current_fg == "#9b1c1c":
            fg = THEME_WARNING
        elif current_fg in DEFAULT_FOREGROUNDS or current_fg.startswith("system"):
            fg = THEME_TEXT
        else:
            fg = str(widget.cget("fg"))
        configure_safe(widget, bg=bg, fg=fg)
    elif isinstance(widget, tk.Button):
        if sys.platform == "darwin":
            configure_safe(
                widget,
                bg=MAC_BUTTON_BG,
                fg=MAC_BUTTON_TEXT,
                activebackground=MAC_BUTTON_ACTIVE_BG,
                activeforeground=MAC_BUTTON_TEXT,
                highlightbackground=THEME_ENTRY_BORDER,
                highlightcolor="#5a8fd8",
                highlightthickness=1,
                relief=tk.RAISED,
                bd=1,
            )
            return

        current_bg = normalized_tk_color(widget.cget("bg"))
        current_fg = normalized_tk_color(widget.cget("fg"))
        accent_button = not is_light_or_system_background(current_bg)
        bg = str(widget.cget("bg")) if accent_button else THEME_BUTTON_BG
        fg = str(widget.cget("fg")) if current_fg not in DEFAULT_FOREGROUNDS else THEME_TEXT
        configure_safe(
            widget,
            bg=bg,
            fg=fg,
            activebackground=bg if accent_button else THEME_BUTTON_ACTIVE_BG,
            activeforeground=fg,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
        )
    elif isinstance(widget, tk.Entry):
        configure_safe(
            widget,
            bg=THEME_ENTRY_BG,
            fg=THEME_TEXT,
            insertbackground=THEME_TEXT,
            selectbackground="#355d90",
            selectforeground=THEME_TEXT,
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground=THEME_ENTRY_BORDER,
            highlightcolor="#5a8fd8",
        )

    for child in widget.winfo_children():
        apply_dark_theme(child)


@dataclass
class UndoSnapshot:
    path: Path
    data: bytes
    index: int
    action: str


@dataclass
class PreviewGeometry:
    original_size: tuple[int, int]
    fitted_size: tuple[int, int]
    offset: tuple[int, int]
    canvas_size: tuple[int, int]


class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("wFunc", ctypes.c_uint),
        ("pFrom", ctypes.c_wchar_p),
        ("pTo", ctypes.c_wchar_p),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", ctypes.c_int),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", ctypes.c_wchar_p),
    ]


FO_DELETE = 3
FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMATION = 0x0010
FOF_NOERRORUI = 0x0400
FOF_SILENT = 0x0004


def default_retry_root_dir() -> Path:
    if sys.platform == "win32":
        return Path(r"D:\等待重新抠图")
    if sys.platform == "darwin":
        return Path.home() / "Pictures" / RETRY_FOLDER_NAME
    return Path.home() / RETRY_FOLDER_NAME


RETRY_ROOT_DIR = default_retry_root_dir()


def load_app_config() -> dict[str, object]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_app_config(config: dict[str, object]) -> None:
    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def config_path_value(config: dict[str, object], key: str) -> Path | None:
    value = config.get(key)
    if not isinstance(value, str) or not value:
        return None
    return Path(value).expanduser()


def save_launcher_history(work_dir: Path, retry_dir: Path) -> None:
    config = load_app_config()
    previous_work_dir = config.get("last_work_dir")
    work_dir_text = str(work_dir)
    config["last_work_dir"] = work_dir_text
    config["last_retry_dir"] = str(retry_dir)
    if previous_work_dir != work_dir_text:
        config["last_index"] = 0
        config["last_image_name"] = ""
    save_app_config(config)


def restore_review_index(work_dir: Path, images: list[Path]) -> int:
    if not images:
        return 0

    config = load_app_config()
    if config.get("last_work_dir") != str(work_dir):
        return 0

    last_image_name = config.get("last_image_name")
    if isinstance(last_image_name, str) and last_image_name:
        for index, image in enumerate(images):
            if image.name == last_image_name:
                return index

    try:
        last_index = int(config.get("last_index", 0))
    except (TypeError, ValueError):
        last_index = 0
    return max(0, min(last_index, len(images) - 1))


def save_review_history(work_dir: Path, retry_dir: Path, index: int, current: Path | None) -> None:
    config = load_app_config()
    config["last_work_dir"] = str(work_dir)
    config["last_retry_dir"] = str(retry_dir)
    config["last_index"] = max(0, index)
    config["last_image_name"] = current.name if current else ""
    save_app_config(config)


def history_text_for(work_dir: Path) -> str | None:
    config = load_app_config()
    if config.get("last_work_dir") != str(work_dir):
        return None

    try:
        raw_index = int(config.get("last_index", 0))
    except (TypeError, ValueError):
        raw_index = 0

    last_image_name = config.get("last_image_name")
    if isinstance(last_image_name, str) and last_image_name:
        return f"上次停在第 {raw_index + 1} 张：{last_image_name}"
    if raw_index > 0:
        return f"上次停在第 {raw_index + 1} 张。"
    return None


def applescript_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def move_to_trash_folder(path: Path) -> None:
    trash_dir = Path.home() / ".Trash" if sys.platform == "darwin" else Path.home() / ".local/share/Trash/files"
    trash_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(unique_path(trash_dir / path.name)))


def send_to_macos_trash(path: Path) -> None:
    script = f'tell application "Finder" to delete POSIX file "{applescript_quote(str(path))}"'
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        move_to_trash_folder(path)


def send_to_recycle_bin(path: Path) -> None:
    if sys.platform == "darwin":
        send_to_macos_trash(path)
        return
    if sys.platform != "win32":
        move_to_trash_folder(path)
        return

    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = str(path) + "\0\0"
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if result != 0:
        raise OSError(f"删除失败，错误码: {result}")
    if op.fAnyOperationsAborted:
        raise OSError("删除操作被中断。")


def open_with_default_app(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.run(["/usr/bin/open", str(path)], check=True)
    else:
        subprocess.run(["xdg-open", str(path)], check=True)


def command_error_text(result: subprocess.CompletedProcess[str]) -> str:
    details = "\n".join(part.strip() for part in (result.stderr, result.stdout) if part and part.strip())
    return details or f"命令退出码：{result.returncode}"


def open_with_photoshop(path: Path) -> None:
    if sys.platform != "darwin":
        raise OSError("PS 打开当前仅支持 macOS。")

    primary = subprocess.run(
        ["/usr/bin/open", "-b", PHOTOSHOP_BUNDLE_ID, str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if primary.returncode == 0:
        return

    if PHOTOSHOP_APP_PATH.exists():
        fallback = subprocess.run(
            ["/usr/bin/open", "-a", str(PHOTOSHOP_APP_PATH), str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if fallback.returncode == 0:
            return
        raise OSError(f"无法用 Photoshop 打开：\n{command_error_text(fallback)}")

    raise OSError(f"找不到 Photoshop，且 bundle id 打开失败：\n{command_error_text(primary)}")


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def done_folder_target(folder: Path) -> Path:
    if folder.name.endswith(DONE_FOLDER_SUFFIX):
        return folder
    return unique_path(folder.with_name(f"{folder.name}{DONE_FOLDER_SUFFIX}"))


def list_images(folder: Path) -> list[Path]:
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS],
        key=lambda p: p.name.lower(),
    )


def count_parent_matches(folder: Path) -> int:
    if not folder.exists() or not folder.is_dir():
        return 0

    parent = folder.parent
    return sum(1 for image in list_images(folder) if (parent / image.name).exists())


def make_checkerboard(size: tuple[int, int], tile: int = 24) -> Image.Image:
    width = max(size[0], 1)
    height = max(size[1], 1)
    canvas = Image.new("RGBA", (width, height), BG_COLOR_1)
    drawer = ImageDraw.Draw(canvas)

    for y in range(0, height, tile):
        for x in range(0, width, tile):
            if ((x // tile) + (y // tile)) % 2:
                drawer.rectangle((x, y, min(x + tile - 1, width - 1), min(y + tile - 1, height - 1)), fill=BG_COLOR_2)
    return canvas


def render_preview(image_path: Path, max_width: int, max_height: int) -> Image.Image:
    max_width = max(max_width, 200)
    max_height = max(max_height, 200)

    with Image.open(image_path) as src:
        image = src.convert("RGBA")

    fitted = ImageOps.contain(image, (max_width - 40, max_height - 40), Image.Resampling.LANCZOS)
    board = make_checkerboard((max_width, max_height))
    offset_x = (max_width - fitted.width) // 2
    offset_y = (max_height - fitted.height) // 2
    board.alpha_composite(fitted, (offset_x, offset_y))
    return board


def compute_preview_geometry(image_path: Path, max_width: int, max_height: int) -> PreviewGeometry:
    max_width = max(max_width, 200)
    max_height = max(max_height, 200)

    with Image.open(image_path) as src:
        original_width, original_height = src.size
        fitted = ImageOps.contain(src.convert("RGBA"), (max_width - 40, max_height - 40), Image.Resampling.LANCZOS)

    offset_x = (max_width - fitted.width) // 2
    offset_y = (max_height - fitted.height) // 2
    return PreviewGeometry(
        original_size=(original_width, original_height),
        fitted_size=fitted.size,
        offset=(offset_x, offset_y),
        canvas_size=(max_width, max_height),
    )


def detect_save_format(path: Path, pil_format: str | None) -> str:
    if pil_format:
        return pil_format.upper()

    mapping = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP",
        ".bmp": "BMP",
    }
    return mapping.get(path.suffix.lower(), "PNG")


def save_image_atomic(image: Image.Image, path: Path, save_format: str) -> None:
    temp_path = path.with_name(f"{path.stem}.__tmp__{path.suffix}")
    save_kwargs: dict[str, object] = {}

    if save_format == "JPEG":
        save_kwargs["quality"] = 100
        save_kwargs["subsampling"] = 0
    elif save_format == "WEBP":
        save_kwargs["lossless"] = True

    image.save(temp_path, format=save_format, **save_kwargs)
    temp_path.replace(path)


def restore_bytes_atomic(path: Path, data: bytes) -> None:
    temp_path = path.with_name(f"{path.stem}.__undo__{path.suffix}")
    temp_path.write_bytes(data)
    temp_path.replace(path)


def invert_image_preserve_alpha(path: Path) -> None:
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        has_alpha = "A" in src.getbands() or "transparency" in src.info

        if has_alpha:
            rgba = src.convert("RGBA")
            r, g, b, a = rgba.split()
            inverted = Image.merge(
                "RGBA",
                (
                    ImageChops.invert(r),
                    ImageChops.invert(g),
                    ImageChops.invert(b),
                    a,
                ),
            )
            output = inverted if save_format != "JPEG" else inverted.convert("RGB")
        else:
            rgb = src.convert("RGB")
            output = ImageChops.invert(rgb)

    save_image_atomic(output, path, save_format)


def black_to_white_preserve_alpha(
    path: Path,
    threshold: int = NEAR_BLACK_THRESHOLD,
) -> None:
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        has_alpha = "A" in src.getbands() or "transparency" in src.info

        if has_alpha:
            rgba = src.convert("RGBA")
            r, g, b, a = rgba.split()
            mask = make_near_black_mask(r, g, b, threshold)
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            output = Image.composite(white, rgba, mask)
            output.putalpha(a)
            output = output if save_format != "JPEG" else output.convert("RGB")
        else:
            rgb = src.convert("RGB")
            r, g, b = rgb.split()
            mask = make_near_black_mask(r, g, b, threshold)
            white = Image.new("RGB", rgb.size, (255, 255, 255))
            output = Image.composite(white, rgb, mask)

    save_image_atomic(output, path, save_format)


def make_near_black_mask(
    r: Image.Image,
    g: Image.Image,
    b: Image.Image,
    threshold: int,
) -> Image.Image:
    threshold = max(0, min(threshold, 255))
    channel_mask = lambda channel: channel.point(lambda value: 255 if value <= threshold else 0)
    return ImageChops.multiply(ImageChops.multiply(channel_mask(r), channel_mask(g)), channel_mask(b))


def whiten_image_preserve_alpha(path: Path) -> None:
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        has_alpha = "A" in src.getbands() or "transparency" in src.info

        if has_alpha:
            rgba = src.convert("RGBA")
            _, _, _, a = rgba.split()
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 0))
            white.putalpha(a)
            output = white if save_format != "JPEG" else white.convert("RGB")
        else:
            output = Image.new("RGB", src.size, (255, 255, 255))

    save_image_atomic(output, path, save_format)


def whiten_selection_preserve_alpha(path: Path, selection_mask: Image.Image) -> None:
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        has_alpha = "A" in src.getbands() or "transparency" in src.info

        mask = selection_mask.convert("L").resize(src.size, Image.Resampling.NEAREST)
        mask = mask.point(lambda value: 255 if value > 0 else 0)

        if has_alpha:
            rgba = src.convert("RGBA")
            alpha = rgba.getchannel("A")
            visible_mask = alpha.point(lambda value: 255 if value > 0 else 0)
            final_mask = ImageChops.multiply(mask, visible_mask)
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 0))
            white.putalpha(alpha)
            output = Image.composite(white, rgba, final_mask)
            output = output if save_format != "JPEG" else output.convert("RGB")
        else:
            rgb = src.convert("RGB")
            white = Image.new("RGB", rgb.size, (255, 255, 255))
            output = Image.composite(white, rgb, mask)

    save_image_atomic(output, path, save_format)


def dilate_mask(mask: Image.Image, radius: int) -> Image.Image:
    radius = max(0, int(radius))
    if radius == 0:
        return mask.copy()
    return mask.filter(ImageFilter.MaxFilter(radius * 2 + 1))


def grow_rgb_by_mask(r: Image.Image, g: Image.Image, b: Image.Image, mask: Image.Image, radius: int) -> tuple[Image.Image, Image.Image, Image.Image]:
    empty = Image.new("L", mask.size, 0)
    grow_filter_size = max(1, int(radius) * 2 + 1)
    return (
        Image.composite(r, empty, mask).filter(ImageFilter.MaxFilter(grow_filter_size)),
        Image.composite(g, empty, mask).filter(ImageFilter.MaxFilter(grow_filter_size)),
        Image.composite(b, empty, mask).filter(ImageFilter.MaxFilter(grow_filter_size)),
    )


def make_non_white_mask(r: Image.Image, g: Image.Image, b: Image.Image, threshold: int = 250) -> Image.Image:
    threshold = max(0, min(threshold, 255))
    white_mask = ImageChops.multiply(
        ImageChops.multiply(
            r.point(lambda value: 255 if value >= threshold else 0),
            g.point(lambda value: 255 if value >= threshold else 0),
        ),
        b.point(lambda value: 255 if value >= threshold else 0),
    )
    return ImageChops.invert(white_mask)


def bolden_image(path: Path, bold_size: int) -> None:
    bold_size = max(1, int(bold_size))
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        has_alpha = "A" in src.getbands() or "transparency" in src.info

        if has_alpha:
            rgba = src.convert("RGBA")
            r, g, b, a = rgba.split()
            foreground_mask = a.point(lambda value: 255 if value > 0 else 0)
            grown_alpha = dilate_mask(a, bold_size)
            grown_r, grown_g, grown_b = grow_rgb_by_mask(r, g, b, foreground_mask, bold_size)
            output = Image.merge("RGBA", (grown_r, grown_g, grown_b, grown_alpha))
            output.alpha_composite(rgba)
            output = output if save_format != "JPEG" else output.convert("RGB")
        else:
            rgb = src.convert("RGB")
            r, g, b = rgb.split()
            foreground_mask = make_non_white_mask(r, g, b)
            grown_mask = dilate_mask(foreground_mask, bold_size)
            grown_r, grown_g, grown_b = grow_rgb_by_mask(r, g, b, foreground_mask, bold_size)
            grown_rgb = Image.merge("RGB", (grown_r, grown_g, grown_b))
            output = Image.composite(grown_rgb, rgb, grown_mask)

    save_image_atomic(output, path, save_format)


def add_white_border(path: Path, border_size: int = WHITE_BORDER_SIZE) -> None:
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        has_alpha = "A" in src.getbands() or "transparency" in src.info

        if has_alpha:
            rgba = src.convert("RGBA")
            expanded = ImageOps.expand(rgba, border=border_size, fill=(255, 255, 255, 0))
            alpha = expanded.getchannel("A")
            border_alpha = alpha.filter(ImageFilter.MaxFilter(border_size * 2 + 1))
            border_only_alpha = ImageChops.subtract(border_alpha, alpha)
            border_layer = Image.new("RGBA", expanded.size, (255, 255, 255, 255))
            border_layer.putalpha(border_only_alpha)
            border_layer.alpha_composite(expanded)
            output = border_layer if save_format != "JPEG" else border_layer.convert("RGB")
        else:
            rgb = src.convert("RGB")
            output = ImageOps.expand(rgb, border=border_size, fill=(255, 255, 255))

    save_image_atomic(output, path, save_format)


def normalize_stroke_points(points: list[tuple[int, int]], size: tuple[int, int]) -> list[tuple[int, int]]:
    width, height = size
    normalized: list[tuple[int, int]] = []
    for x, y in points:
        point = (
            max(0, min(width - 1, int(round(x)))),
            max(0, min(height - 1, int(round(y)))),
        )
        if not normalized or point != normalized[-1]:
            normalized.append(point)
    return normalized


def draw_round_stroke(
    drawer: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    brush_size: int,
    fill: int | tuple[int, int, int],
) -> None:
    if not points:
        return

    brush_size = max(1, int(brush_size))
    radius = max(1, brush_size // 2)
    if len(points) >= 2:
        drawer.line(points, fill=fill, width=brush_size, joint="curve")
    for x, y in points:
        drawer.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def erase_image_stroke(path: Path, points: list[tuple[int, int]], brush_size: int) -> None:
    with Image.open(path) as src:
        save_format = detect_save_format(path, src.format)
        stroke_points = normalize_stroke_points(points, src.size)
        if not stroke_points:
            return

        if save_format in ERASER_TRANSPARENT_FORMATS:
            output = src.convert("RGBA")
            alpha = output.getchannel("A")
            draw_round_stroke(ImageDraw.Draw(alpha), stroke_points, brush_size, 0)
            output.putalpha(alpha)
        else:
            output = src.convert("RGB")
            draw_round_stroke(ImageDraw.Draw(output), stroke_points, brush_size, (255, 255, 255))

    save_image_atomic(output, path, save_format)


class ReviewApp:
    def __init__(self, work_dir: Path, retry_dir: Path) -> None:
        self.work_dir = work_dir
        self.parent_dir = work_dir.parent
        self.retry_dir = retry_dir
        self.images = list_images(work_dir)
        self.index = restore_review_index(work_dir, self.images)
        self.photo: ImageTk.PhotoImage | None = None
        self.resize_job: str | None = None
        self.status_notice = ""
        self.completion_prompted = False
        self.undo_stack: list[UndoSnapshot] = []
        self.preview_geometry: PreviewGeometry | None = None
        self.selection_mode: str | None = None
        self.selection_mask: Image.Image | None = None
        self.selection_kind: str | None = None
        self.selection_rect_image: tuple[int, int, int, int] | None = None
        self.selection_polygon_image: list[tuple[int, int]] = []
        self.drag_start_canvas: tuple[int, int] | None = None
        self.drag_points_canvas: list[tuple[int, int]] = []
        self.eraser_size = ERASER_DEFAULT_SIZE
        self.eraser_points_image: list[tuple[int, int]] = []
        self.eraser_points_canvas: list[tuple[int, int]] = []

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry("1280x920")
        self.root.minsize(900, 700)
        install_dark_theme(self.root)

        self.header_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.work_dir_var = tk.StringVar(value=self.processing_folder_text())
        self.jump_var = tk.StringVar()
        self.eraser_button_var = tk.StringVar(value=self.eraser_button_text())

        header = tk.Label(
            self.root,
            textvariable=self.header_var,
            font=(UI_FONT, 14, "bold"),
            anchor="w",
            padx=16,
            pady=10,
        )
        header.pack(fill="x")

        self.preview_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.preview_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.image_canvas = tk.Canvas(
            self.preview_frame,
            bg="#f0f0f0",
            highlightthickness=0,
            bd=0,
        )
        self.image_canvas.pack(fill="both", expand=True)

        controls = tk.Frame(self.root, padx=10, pady=6)
        controls.pack(fill="x")

        left_controls = tk.Frame(controls)
        left_controls.pack(side="left", anchor="nw", fill="x")

        right_controls = tk.Frame(controls)
        right_controls.pack(side="right", anchor="ne", fill="x", expand=True, padx=(12, 0))

        nav_controls = tk.Frame(left_controls)
        nav_controls.pack(fill="x", pady=(0, 6))

        jump_controls = tk.Frame(left_controls)
        jump_controls.pack(fill="x")

        selection_controls = tk.Frame(right_controls)
        selection_controls.pack(fill="x", pady=(0, 6), anchor="e")

        edit_controls = tk.Frame(right_controls)
        edit_controls.pack(fill="x", anchor="e")

        tk.Button(
            nav_controls,
            text="上一张 ←",
            width=13,
            command=self.prev_image,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            nav_controls,
            text="保留 / 下一张 空格",
            width=18,
            command=self.keep_current,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            nav_controls,
            text="打开当前图 O",
            width=13,
            command=self.open_current_preview,
            font=(UI_FONT, 11),
            bg="#4b6b88",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            nav_controls,
            text="PS 打开 P",
            width=10,
            command=self.open_current_in_photoshop,
            font=(UI_FONT, 11),
            bg="#5d4a8b",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            nav_controls,
            text="刷新当前图 F5",
            width=14,
            command=self.reload_current_preview,
            font=(UI_FONT, 11),
            bg="#3f7a5f",
            fg="white",
        ).pack(side="left")

        tk.Button(
            jump_controls,
            text="删预览并回退原图 D",
            width=18,
            command=self.reject_current,
            font=(UI_FONT, 11),
            bg="#cc423c",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            jump_controls,
            text="仅删除预览 X",
            width=13,
            command=self.delete_preview_only,
            font=(UI_FONT, 11),
            bg="#8b5a2b",
            fg="white",
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            jump_controls,
            text="跳到",
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 4))

        self.jump_entry = tk.Entry(
            jump_controls,
            textvariable=self.jump_var,
            width=6,
            font=(UI_FONT, 11),
        )
        self.jump_entry.pack(side="left")
        self.jump_entry.bind("<Return>", self.jump_to_entered)

        tk.Label(
            jump_controls,
            text="张",
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(4, 6))

        tk.Button(
            jump_controls,
            text="跳 G",
            width=7,
            command=self.jump_to_entered,
            font=(UI_FONT, 11),
            bg="#375a7f",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Label(
            jump_controls,
            text=f"共 {len(self.images)} 张",
            font=(UI_FONT, 10),
            fg="#555555",
        ).pack(side="left")

        tk.Button(
            selection_controls,
            text="矩形选区 R",
            width=12,
            command=lambda: self.set_selection_mode("rect"),
            font=(UI_FONT, 11),
            bg="#4f6f45",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            selection_controls,
            text="自由选区 F",
            width=12,
            command=lambda: self.set_selection_mode("free"),
            font=(UI_FONT, 11),
            bg="#5f5f91",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            selection_controls,
            textvariable=self.eraser_button_var,
            width=14,
            command=lambda: self.set_selection_mode("erase"),
            font=(UI_FONT, 11),
            bg="#b64f3b",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            selection_controls,
            text="选区转纯白",
            width=13,
            command=self.whiten_selection_current,
            font=(UI_FONT, 11),
            bg="#2f7d64",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            selection_controls,
            text="清除选区",
            width=11,
            command=self.clear_selection,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            selection_controls,
            text="撤销 Ctrl+Z/⌘Z",
            width=13,
            command=self.undo_last,
            font=(UI_FONT, 11),
            bg="#555555",
            fg="white",
        ).pack(side="left")

        tk.Button(
            edit_controls,
            text="反相 I",
            width=11,
            command=self.invert_current,
            font=(UI_FONT, 11),
            bg="#2f6fda",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            edit_controls,
            text="转纯白 W",
            width=11,
            command=self.whiten_current,
            font=(UI_FONT, 11),
            bg="#3a8f3a",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            edit_controls,
            text="黑转白 K",
            width=11,
            command=self.black_to_white_current,
            font=(UI_FONT, 11),
            bg="#1f7a7a",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            edit_controls,
            text="加粗1px B",
            width=11,
            command=lambda: self.bolden_current(BOLDEN_SIZE_1),
            font=(UI_FONT, 11),
            bg="#7a5c1f",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            edit_controls,
            text="加粗2px 2",
            width=11,
            command=lambda: self.bolden_current(BOLDEN_SIZE_2),
            font=(UI_FONT, 11),
            bg="#8a3f24",
            fg="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            edit_controls,
            text="加白边 N",
            width=11,
            command=self.add_border_current,
            font=(UI_FONT, 11),
            bg="#6f4fc9",
            fg="white",
        ).pack(side="left")

        tk.Label(
            right_controls,
            textvariable=self.work_dir_var,
            anchor="e",
            justify="right",
            wraplength=780,
            font=(UI_FONT, 9),
            fg="#555555",
        ).pack(fill="x", pady=(4, 0), anchor="e")

        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            justify="left",
            padx=10,
            pady=4,
            font=(UI_FONT, 9),
        )
        status.pack(fill="x")

        self.root.bind("<space>", lambda event: self.keep_current())
        self.root.bind("<Right>", lambda event: self.keep_current())
        self.root.bind("<Return>", lambda event: self.keep_current())
        self.root.bind("<Left>", lambda event: self.prev_image())
        self.root.bind("<BackSpace>", lambda event: self.prev_image())
        self.root.bind("<Key-o>", lambda event: self.open_current_preview())
        self.root.bind("<Key-O>", lambda event: self.open_current_preview())
        self.root.bind("<Key-p>", lambda event: self.open_current_in_photoshop())
        self.root.bind("<Key-P>", lambda event: self.open_current_in_photoshop())
        self.root.bind("<F5>", lambda event: self.reload_current_preview())
        self.root.bind("<Key-g>", self.focus_jump_entry)
        self.root.bind("<Key-G>", self.focus_jump_entry)
        self.root.bind("<Key-r>", lambda event: self.set_selection_mode("rect"))
        self.root.bind("<Key-R>", lambda event: self.set_selection_mode("rect"))
        self.root.bind("<Key-f>", lambda event: self.set_selection_mode("free"))
        self.root.bind("<Key-F>", lambda event: self.set_selection_mode("free"))
        self.root.bind("<Key-e>", lambda event: self.set_selection_mode("erase"))
        self.root.bind("<Key-E>", lambda event: self.set_selection_mode("erase"))
        self.root.bind("<Key-bracketleft>", lambda event: self.adjust_eraser_size(-ERASER_SIZE_STEP))
        self.root.bind("<Key-bracketright>", lambda event: self.adjust_eraser_size(ERASER_SIZE_STEP))
        self.root.bind("<Key-i>", lambda event: self.invert_current())
        self.root.bind("<Key-I>", lambda event: self.invert_current())
        self.root.bind("<Key-w>", lambda event: self.whiten_current())
        self.root.bind("<Key-W>", lambda event: self.whiten_current())
        self.root.bind("<Key-k>", lambda event: self.black_to_white_current())
        self.root.bind("<Key-K>", lambda event: self.black_to_white_current())
        self.root.bind("<Key-b>", lambda event: self.bolden_current(BOLDEN_SIZE_1))
        self.root.bind("<Key-B>", lambda event: self.bolden_current(BOLDEN_SIZE_1))
        self.root.bind("<Key-2>", lambda event: self.bolden_current(BOLDEN_SIZE_2))
        self.root.bind("<Key-n>", lambda event: self.add_border_current())
        self.root.bind("<Key-N>", lambda event: self.add_border_current())
        self.root.bind("<Control-z>", lambda event: self.undo_last())
        self.root.bind("<Control-Z>", lambda event: self.undo_last())
        self.root.bind("<Command-z>", lambda event: self.undo_last())
        self.root.bind("<Command-Z>", lambda event: self.undo_last())
        self.root.bind("<Key-u>", lambda event: self.undo_last())
        self.root.bind("<Key-U>", lambda event: self.undo_last())
        self.root.bind("<Delete>", lambda event: self.reject_current())
        self.root.bind("<Key-d>", lambda event: self.reject_current())
        self.root.bind("<Key-D>", lambda event: self.reject_current())
        self.root.bind("<Key-x>", lambda event: self.delete_preview_only())
        self.root.bind("<Key-X>", lambda event: self.delete_preview_only())
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Command-q>", self.quit_app)
        self.root.bind("<Command-Q>", self.quit_app)
        self.image_canvas.bind("<Configure>", self.on_resize)
        self.image_canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.image_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        apply_dark_theme(self.root)
        self.refresh()

    def processing_folder_text(self) -> str:
        return f"当前处理文件夹：{self.work_dir}"

    def update_work_dir_label(self) -> None:
        self.work_dir_var.set(self.processing_folder_text())

    def mark_work_dir_done(self) -> None:
        old_dir = self.work_dir
        new_dir = done_folder_target(old_dir)
        if new_dir == old_dir:
            self.status_notice = f"当前文件夹已经带有 {DONE_FOLDER_SUFFIX} 后缀：{old_dir}"
            self.refresh()
            return

        try:
            old_dir.rename(new_dir)
        except Exception as exc:
            messagebox.showerror("标记失败", f"文件夹重命名失败：\n{old_dir}\n\n{exc}")
            return

        self.work_dir = new_dir
        self.parent_dir = new_dir.parent
        self.images = [new_dir / image.name for image in self.images]
        self.update_work_dir_label()
        save_review_history(self.work_dir, self.retry_dir, self.index, self.current_image())
        self.status_notice = f"已标记已查图：{new_dir}"
        self.refresh()

    def prompt_completion_if_needed(self) -> None:
        if self.completion_prompted:
            self.status_notice = "已查完。"
            self.refresh()
            return

        self.completion_prompted = True
        should_mark = messagebox.askyesno(
            "已查完",
            f"已查完，是否标记已查图？\n\n选择“是”会把当前文件夹重命名，加上后缀 {DONE_FOLDER_SUFFIX}。",
        )
        if should_mark:
            self.mark_work_dir_done()
            return

        self.status_notice = "已查完，未标记文件夹。"
        self.refresh()

    def on_resize(self, _event: tk.Event) -> None:
        if self.resize_job:
            try:
                self.root.after_cancel(self.resize_job)
            except Exception:
                pass
        self.resize_job = self.root.after(120, self.refresh_image_only)

    def current_image(self) -> Path | None:
        if not self.images:
            return None
        self.index = max(0, min(self.index, len(self.images) - 1))
        return self.images[self.index]

    def reset_selection_state(self) -> None:
        self.selection_mask = None
        self.selection_kind = None
        self.selection_rect_image = None
        self.selection_polygon_image = []
        self.drag_start_canvas = None
        self.drag_points_canvas = []
        self.eraser_points_image = []
        self.eraser_points_canvas = []

    def eraser_button_text(self) -> str:
        return f"橡皮擦 E {self.eraser_size}px"

    def update_eraser_button_text(self) -> None:
        self.eraser_button_var.set(self.eraser_button_text())

    def set_selection_mode(self, mode: str) -> None:
        if mode not in {"rect", "free", "erase"}:
            return
        self.selection_mode = mode
        if mode == "rect":
            self.status_notice = "已切到矩形选区：在预览图上按住鼠标拖出矩形。"
        elif mode == "free":
            self.status_notice = "已切到自由选区：按住鼠标沿区域画一圈，松开后自动闭合。"
        else:
            self.reset_selection_state()
            self.image_canvas.delete("selection")
            self.image_canvas.delete("selection_live")
            self.image_canvas.delete("eraser_live")
            self.status_notice = f"已切到橡皮擦：按住鼠标拖动擦除，笔刷 {self.eraser_size}px，[/] 调大小。"
        self.refresh()

    def clear_selection(self) -> None:
        self.reset_selection_state()
        self.image_canvas.delete("selection")
        self.image_canvas.delete("selection_live")
        self.image_canvas.delete("eraser_live")
        self.status_notice = "已清除选区。"
        self.refresh()

    def adjust_eraser_size(self, delta: int) -> str:
        old_size = self.eraser_size
        self.eraser_size = max(ERASER_MIN_SIZE, min(ERASER_MAX_SIZE, self.eraser_size + delta))
        self.update_eraser_button_text()
        if self.eraser_size != old_size:
            self.status_notice = f"橡皮擦笔刷：{self.eraser_size}px。"
            self.refresh()
        return "break"

    def is_canvas_point_inside_image(self, x: int, y: int) -> bool:
        geometry = self.preview_geometry
        if geometry is None:
            return False

        offset_x, offset_y = geometry.offset
        fitted_width, fitted_height = geometry.fitted_size
        return offset_x <= x <= offset_x + fitted_width and offset_y <= y <= offset_y + fitted_height

    def canvas_to_image_point_if_inside(self, x: int, y: int) -> tuple[int, int] | None:
        if not self.is_canvas_point_inside_image(x, y):
            return None
        return self.canvas_to_image_point(x, y)

    def eraser_canvas_width(self) -> int:
        geometry = self.preview_geometry
        if geometry is None:
            return max(1, self.eraser_size)

        original_width, original_height = geometry.original_size
        fitted_width, fitted_height = geometry.fitted_size
        if original_width <= 0 or original_height <= 0:
            return max(1, self.eraser_size)

        scale = min(fitted_width / original_width, fitted_height / original_height)
        return max(1, round(self.eraser_size * scale))

    def draw_eraser_live_overlay(self) -> None:
        self.image_canvas.delete("eraser_live")
        if not self.eraser_points_canvas:
            return

        width = self.eraser_canvas_width()
        radius = max(1, width // 2)
        if len(self.eraser_points_canvas) == 1:
            x, y = self.eraser_points_canvas[0]
            self.image_canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline="#ff4d4d",
                width=2,
                tags="eraser_live",
            )
            return

        coords: list[int] = []
        for x, y in self.eraser_points_canvas:
            coords.extend((x, y))
        self.image_canvas.create_line(
            *coords,
            fill="#ff4d4d",
            width=width,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=True,
            tags="eraser_live",
        )

    def canvas_to_image_point(self, x: int, y: int) -> tuple[int, int] | None:
        geometry = self.preview_geometry
        if geometry is None:
            return None

        offset_x, offset_y = geometry.offset
        fitted_width, fitted_height = geometry.fitted_size
        original_width, original_height = geometry.original_size
        if fitted_width <= 0 or fitted_height <= 0:
            return None

        image_x = round((x - offset_x) * original_width / fitted_width)
        image_y = round((y - offset_y) * original_height / fitted_height)
        image_x = max(0, min(original_width - 1, image_x))
        image_y = max(0, min(original_height - 1, image_y))
        return image_x, image_y

    def image_to_canvas_point(self, x: int, y: int) -> tuple[int, int] | None:
        geometry = self.preview_geometry
        if geometry is None:
            return None

        offset_x, offset_y = geometry.offset
        fitted_width, fitted_height = geometry.fitted_size
        original_width, original_height = geometry.original_size
        if original_width <= 0 or original_height <= 0:
            return None

        canvas_x = round(offset_x + x * fitted_width / original_width)
        canvas_y = round(offset_y + y * fitted_height / original_height)
        return canvas_x, canvas_y

    def make_rect_selection_mask(self, start: tuple[int, int], end: tuple[int, int]) -> Image.Image | None:
        geometry = self.preview_geometry
        if geometry is None:
            return None

        x1, y1 = start
        x2, y2 = end
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))
        if right - left < 2 or bottom - top < 2:
            return None

        mask = Image.new("L", geometry.original_size, 0)
        ImageDraw.Draw(mask).rectangle((left, top, right, bottom), fill=255)
        self.selection_kind = "rect"
        self.selection_rect_image = (left, top, right, bottom)
        self.selection_polygon_image = []
        return mask

    def make_free_selection_mask(self, points: list[tuple[int, int]]) -> Image.Image | None:
        geometry = self.preview_geometry
        if geometry is None or len(points) < 3:
            return None

        deduped: list[tuple[int, int]] = []
        for point in points:
            if not deduped or point != deduped[-1]:
                deduped.append(point)
        if len(deduped) < 3:
            return None

        mask = Image.new("L", geometry.original_size, 0)
        ImageDraw.Draw(mask).polygon(deduped, fill=255)
        self.selection_kind = "free"
        self.selection_rect_image = None
        self.selection_polygon_image = deduped
        return mask

    def draw_selection_overlay(self) -> None:
        self.image_canvas.delete("selection")
        geometry = self.preview_geometry
        if geometry is None or self.selection_mask is None:
            return

        if self.selection_kind == "rect" and self.selection_rect_image:
            left, top, right, bottom = self.selection_rect_image
            p1 = self.image_to_canvas_point(left, top)
            p2 = self.image_to_canvas_point(right, bottom)
            if p1 and p2:
                self.image_canvas.create_rectangle(
                    p1[0],
                    p1[1],
                    p2[0],
                    p2[1],
                    outline="#00a2ff",
                    width=2,
                    dash=(6, 3),
                    tags="selection",
                )
        elif self.selection_kind == "free" and len(self.selection_polygon_image) >= 3:
            canvas_points: list[int] = []
            for x, y in self.selection_polygon_image:
                point = self.image_to_canvas_point(x, y)
                if point:
                    canvas_points.extend(point)
            if len(canvas_points) >= 6:
                self.image_canvas.create_polygon(
                    *canvas_points,
                    outline="#00a2ff",
                    fill="",
                    width=2,
                    tags="selection",
                )

    def on_eraser_press(self, event: tk.Event) -> str | None:
        if self.current_image() is None:
            return None

        point = self.canvas_to_image_point_if_inside(event.x, event.y)
        if point is None:
            self.eraser_points_image = []
            self.eraser_points_canvas = []
            self.image_canvas.delete("eraser_live")
            return "break"

        self.eraser_points_image = [point]
        self.eraser_points_canvas = [(event.x, event.y)]
        self.draw_eraser_live_overlay()
        return "break"

    def on_eraser_drag(self, event: tk.Event) -> str | None:
        if not self.eraser_points_image:
            return "break"

        point = self.canvas_to_image_point_if_inside(event.x, event.y)
        if point is None:
            return "break"

        last_x, last_y = self.eraser_points_image[-1]
        if abs(point[0] - last_x) + abs(point[1] - last_y) >= 1:
            self.eraser_points_image.append(point)
            self.eraser_points_canvas.append((event.x, event.y))
            self.draw_eraser_live_overlay()
        return "break"

    def on_eraser_release(self, event: tk.Event) -> str | None:
        if not self.eraser_points_image:
            return "break"

        point = self.canvas_to_image_point_if_inside(event.x, event.y)
        if point is not None and point != self.eraser_points_image[-1]:
            self.eraser_points_image.append(point)
            self.eraser_points_canvas.append((event.x, event.y))

        current = self.current_image()
        points = self.eraser_points_image.copy()
        brush_size = self.eraser_size
        self.eraser_points_image = []
        self.eraser_points_canvas = []
        self.image_canvas.delete("eraser_live")
        if current is None or not points:
            return "break"

        self.apply_current_edit(
            "橡皮擦",
            "橡皮擦失败",
            lambda path: erase_image_stroke(path, points, brush_size),
            f"已橡皮擦：{current.name}（{brush_size}px）",
        )
        return "break"

    def on_canvas_press(self, event: tk.Event) -> str | None:
        if self.selection_mode == "erase":
            return self.on_eraser_press(event)
        if self.selection_mode is None or self.current_image() is None:
            return None

        self.drag_start_canvas = (event.x, event.y)
        self.drag_points_canvas = [(event.x, event.y)]
        self.image_canvas.delete("selection_live")
        if self.selection_mode == "rect":
            self.image_canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="#ffcc00",
                width=2,
                dash=(4, 3),
                tags="selection_live",
            )
        else:
            self.image_canvas.create_line(
                event.x,
                event.y,
                event.x,
                event.y,
                fill="#ffcc00",
                width=2,
                tags="selection_live",
            )
        return "break"

    def on_canvas_drag(self, event: tk.Event) -> str | None:
        if self.selection_mode == "erase":
            return self.on_eraser_drag(event)
        if self.selection_mode is None or self.drag_start_canvas is None:
            return None

        if self.selection_mode == "rect":
            start_x, start_y = self.drag_start_canvas
            self.image_canvas.coords("selection_live", start_x, start_y, event.x, event.y)
        else:
            last_x, last_y = self.drag_points_canvas[-1]
            if abs(event.x - last_x) + abs(event.y - last_y) >= 3:
                self.drag_points_canvas.append((event.x, event.y))
                coords: list[int] = []
                for x, y in self.drag_points_canvas:
                    coords.extend((x, y))
                self.image_canvas.coords("selection_live", *coords)
        return "break"

    def on_canvas_release(self, event: tk.Event) -> str | None:
        if self.selection_mode == "erase":
            return self.on_eraser_release(event)
        if self.selection_mode is None or self.drag_start_canvas is None:
            return None

        self.image_canvas.delete("selection_live")
        if self.selection_mode == "rect":
            start = self.canvas_to_image_point(*self.drag_start_canvas)
            end = self.canvas_to_image_point(event.x, event.y)
            mask = self.make_rect_selection_mask(start, end) if start and end else None
        else:
            self.drag_points_canvas.append((event.x, event.y))
            image_points = [
                point
                for point in (self.canvas_to_image_point(x, y) for x, y in self.drag_points_canvas)
                if point is not None
            ]
            mask = self.make_free_selection_mask(image_points)

        self.drag_start_canvas = None
        self.drag_points_canvas = []
        if mask is None:
            self.status_notice = "选区太小或无效，请重新框选。"
            self.refresh()
            return "break"

        self.selection_mask = mask
        self.status_notice = "已创建选区，可点击“选区转纯白”。"
        self.refresh()
        return "break"

    def push_undo(self, path: Path, action: str) -> None:
        self.undo_stack.append(UndoSnapshot(path=path, data=path.read_bytes(), index=self.index, action=action))
        if len(self.undo_stack) > MAX_UNDO_STEPS:
            self.undo_stack.pop(0)

    def forget_undo_for_path(self, path: Path) -> None:
        self.undo_stack = [snapshot for snapshot in self.undo_stack if snapshot.path != path]

    def apply_current_edit(
        self,
        action: str,
        error_title: str,
        processor: Callable[[Path], None],
        success_notice: str,
    ) -> None:
        current = self.current_image()
        if current is None:
            return

        try:
            self.push_undo(current, action)
        except Exception as exc:
            messagebox.showerror("无法创建撤销记录", f"未修改图片。\n\n{exc}")
            return

        try:
            processor(current)
        except Exception as exc:
            self.undo_stack.pop()
            messagebox.showerror(error_title, str(exc))
            return

        self.status_notice = success_notice
        self.refresh()

    def undo_last(self) -> None:
        if not self.undo_stack:
            self.status_notice = "没有可撤销的图片修改。"
            self.refresh()
            return

        snapshot = self.undo_stack.pop()
        try:
            restore_bytes_atomic(snapshot.path, snapshot.data)
        except Exception as exc:
            messagebox.showerror("撤销失败", str(exc))
            return

        if snapshot.path in self.images:
            self.index = self.images.index(snapshot.path)
        elif snapshot.path.exists() and snapshot.path.suffix.lower() in SUPPORTED_EXTS:
            insert_at = min(snapshot.index, len(self.images))
            self.images.insert(insert_at, snapshot.path)
            self.index = insert_at

        self.status_notice = f"已撤销：{snapshot.action}（{snapshot.path.name}）"
        self.refresh()

    def refresh(self) -> None:
        current = self.current_image()
        save_review_history(self.work_dir, self.retry_dir, self.index, current)
        if current is None:
            self.header_var.set("当前文件夹没有可处理图片了")
            done_text = "已处理完成。按 Command+Q 退出，或点左上角红点关闭。"
            if self.status_notice:
                done_text = f"{self.status_notice}\n{done_text}"
                self.status_notice = ""
            self.status_var.set(done_text)
            self.photo = None
            self.image_canvas.delete("all")
            self.image_canvas.create_text(
                max(self.image_canvas.winfo_width() // 2, 150),
                max(self.image_canvas.winfo_height() // 2, 100),
                text="处理完成",
                font=(UI_FONT, 24, "bold"),
                fill=THEME_MUTED,
            )
            if not self.completion_prompted:
                self.root.after_idle(self.prompt_completion_if_needed)
            return

        self.update_work_dir_label()
        self.header_var.set(f"[{self.index + 1}/{len(self.images)}] {current.name}")
        base_text = (
            f"回退目录：{self.retry_dir}    空格/回车：下一张    P：PS打开    F5：刷新    R/F：矩形/自由选区    E：橡皮擦    [/]：调笔刷    G：跳转    Ctrl+Z/⌘Z/U：撤销    Esc：退全屏    ⌘Q：退出"
        )
        if self.status_notice:
            self.status_var.set(f"{self.status_notice}\n{base_text}")
            self.status_notice = ""
        else:
            self.status_var.set(base_text)
        self.refresh_image_only()

    def refresh_image_only(self) -> None:
        self.resize_job = None
        current = self.current_image()
        if current is None:
            return

        width = self.image_canvas.winfo_width()
        height = self.image_canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        self.preview_geometry = compute_preview_geometry(current, width, height)
        preview = render_preview(current, width, height)
        self.photo = ImageTk.PhotoImage(preview)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(width // 2, height // 2, image=self.photo, anchor="center")
        self.draw_selection_overlay()

    def keep_current(self) -> None:
        if not self.images:
            return
        if self.index < len(self.images) - 1:
            self.reset_selection_state()
            self.index += 1
            self.refresh()
        else:
            self.prompt_completion_if_needed()

    def prev_image(self) -> None:
        if not self.images:
            return
        if self.index > 0:
            self.reset_selection_state()
            self.index -= 1
            self.refresh()

    def focus_jump_entry(self, _event: tk.Event | None = None) -> str:
        self.jump_var.set(str(self.index + 1 if self.images else ""))
        self.jump_entry.focus_set()
        self.jump_entry.selection_range(0, tk.END)
        return "break"

    def jump_to_entered(self, _event: tk.Event | None = None) -> str:
        if not self.images:
            return "break"

        text = self.jump_var.get().strip()
        try:
            target = int(text)
        except ValueError:
            self.status_notice = f"跳转失败：请输入 1 到 {len(self.images)} 之间的数字。"
            self.refresh()
            return "break"

        if target < 1 or target > len(self.images):
            self.status_notice = f"跳转失败：当前只有 {len(self.images)} 张，请输入 1 到 {len(self.images)}。"
            self.refresh()
            return "break"

        if self.index != target - 1:
            self.reset_selection_state()
        self.index = target - 1
        self.status_notice = f"已跳转到第 {target} 张。"
        self.refresh()
        return "break"

    def open_current_preview(self) -> None:
        current = self.current_image()
        if current is None:
            return

        if not current.exists():
            messagebox.showerror("打开失败", f"当前图片不存在：\n{current}")
            return

        try:
            open_with_default_app(current)
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))

    def open_current_in_photoshop(self) -> None:
        current = self.current_image()
        if current is None:
            return

        if not current.exists():
            messagebox.showerror("打开 Photoshop 失败", f"当前图片不存在：\n{current}")
            return

        try:
            open_with_photoshop(current)
        except Exception as exc:
            messagebox.showerror("打开 Photoshop 失败", str(exc))

    def reload_current_preview(self) -> None:
        current = self.current_image()
        if current is None:
            return

        if not current.exists():
            messagebox.showerror("刷新失败", f"当前图片不存在：\n{current}")
            return

        self.reset_selection_state()
        self.status_notice = f"已刷新当前图：{current.name}"
        self.refresh()

    def invert_current(self) -> None:
        current = self.current_image()
        if current is None:
            return

        self.apply_current_edit(
            "反相",
            "反相失败",
            invert_image_preserve_alpha,
            f"已反相：{current.name}",
        )

    def whiten_current(self) -> None:
        current = self.current_image()
        if current is None:
            return

        self.apply_current_edit(
            "转纯白",
            "转纯白失败",
            whiten_image_preserve_alpha,
            f"已转纯白：{current.name}",
        )

    def whiten_selection_current(self) -> None:
        current = self.current_image()
        if current is None:
            return
        if self.selection_mask is None:
            self.status_notice = "还没有选区。先点“矩形选区 R”或“自由选区 F”，再拖出区域。"
            self.refresh()
            return

        mask = self.selection_mask.copy()
        self.apply_current_edit(
            "选区转纯白",
            "选区转纯白失败",
            lambda path: whiten_selection_preserve_alpha(path, mask),
            f"已把选区转纯白：{current.name}",
        )

    def black_to_white_current(self) -> None:
        current = self.current_image()
        if current is None:
            return

        self.apply_current_edit(
            "黑/近黑转白",
            "黑转白失败",
            black_to_white_preserve_alpha,
            f"已把黑/近黑像素转白：{current.name}（R/G/B都≤{NEAR_BLACK_THRESHOLD}）",
        )

    def bolden_current(self, bold_size: int) -> None:
        current = self.current_image()
        if current is None:
            return

        self.apply_current_edit(
            f"加粗{bold_size}px",
            "加粗失败",
            lambda path: bolden_image(path, bold_size),
            f"已加粗 {bold_size}px：{current.name}",
        )

    def add_border_current(self) -> None:
        current = self.current_image()
        if current is None:
            return

        self.apply_current_edit(
            "加白边",
            "加白边失败",
            add_white_border,
            f"已加 {WHITE_BORDER_SIZE}px 白边：{current.name}",
        )

    def exit_fullscreen(self, _event: tk.Event | None = None) -> None:
        try:
            self.root.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        try:
            self.root.state("normal")
        except tk.TclError:
            pass
        self.status_notice = "已执行退出全屏。要关闭程序请按 Command+Q，或点左上角红点。"
        self.refresh()

    def quit_app(self, _event: tk.Event | None = None) -> str:
        self.root.destroy()
        return "break"

    def remove_current_from_queue(self) -> None:
        self.reset_selection_state()
        self.images.pop(self.index)
        if self.index >= len(self.images):
            self.index = max(0, len(self.images) - 1)

    def delete_preview_only(self) -> None:
        current = self.current_image()
        if current is None:
            return

        try:
            send_to_recycle_bin(current)
        except Exception as exc:
            messagebox.showerror("删除失败", str(exc))
            return

        self.forget_undo_for_path(current)
        removed_name = current.name
        self.remove_current_from_queue()
        self.status_notice = f"仅删除了预览图：{removed_name}"
        self.refresh()

    def reject_current(self) -> None:
        current = self.current_image()
        if current is None:
            return

        original = self.parent_dir / current.name
        retry_existing = self.retry_dir / current.name
        moved_to: Path | None = None
        original_target = original

        if not original.exists() and not retry_existing.exists():
            messagebox.showerror(
                "找不到原图",
                f"上一层没找到同名原图：\n{original}\n\n回退目录里也没找到：\n{retry_existing}",
            )
            return

        try:
            if original.exists():
                self.retry_dir.mkdir(parents=True, exist_ok=True)
                moved_to = unique_path(self.retry_dir / current.name)
                shutil.move(str(original), str(moved_to))

            send_to_recycle_bin(current)
        except Exception as exc:
            if moved_to and moved_to.exists() and not original_target.exists():
                try:
                    shutil.move(str(moved_to), str(original_target))
                except Exception:
                    pass
            messagebox.showerror("操作失败", str(exc))
            return

        self.forget_undo_for_path(current)
        removed_name = current.name
        self.remove_current_from_queue()

        if moved_to:
            self.status_notice = f"已删除预览图，并把原图移到：{moved_to}"
        else:
            self.status_notice = f"预览图已删除，原图之前已经在回退目录里：{self.retry_dir / removed_name}"

        self.refresh()

    def run(self) -> None:
        self.root.mainloop()


class LauncherApp:
    def __init__(self, initial_dir: Path) -> None:
        config = load_app_config()
        saved_dir = config_path_value(config, "last_work_dir")
        saved_retry_dir = config_path_value(config, "last_retry_dir")
        self.selected_dir = saved_dir if saved_dir and saved_dir.exists() else initial_dir
        self.selected_retry_dir = saved_retry_dir if saved_retry_dir else RETRY_ROOT_DIR
        self.start_paths: tuple[Path, Path] | None = None

        self.root = tk.Tk()
        self.root.title(f"{WINDOW_TITLE} - 首页")
        self.root.geometry("920x640")
        self.root.minsize(820, 560)
        install_dark_theme(self.root)

        self.folder_var = tk.StringVar()
        self.retry_var = tk.StringVar()
        self.status_var = tk.StringVar()

        outer = tk.Frame(self.root, padx=22, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text=WINDOW_TITLE,
            font=(UI_FONT, 20, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        tk.Label(
            outer,
            text="使用说明",
            font=(UI_FONT, 13, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 6))

        instructions = (
            "1. 先选择要检查的子文件夹，例如：透明背景。\n"
            "2. 这个子文件夹里放预览图；它的上一层放同名原图。\n"
            "3. 进入查图页后：空格下一张，R 矩形选区，F 自由选区，选区转纯白，E 橡皮擦，[/] 调笔刷，G 跳转输入框，O 打开当前图，P 用 PS 打开当前图，F5 刷新当前图，I 反相，W 转纯白，K 黑/近黑转白，B 加粗1px，2 加粗2px，N 加白边，Ctrl+Z/⌘Z/U 撤销，D 删除预览并把原图移到回退目录，X 仅删除预览图，Esc 退全屏，⌘Q 退出。\n"
            "4. 图片修改会直接覆盖当前图，但本次运行内最近的修改可撤销。"
        )
        tk.Label(
            outer,
            text=instructions,
            justify="left",
            anchor="w",
            bg="#f6f6f6",
            padx=14,
            pady=12,
            font=(UI_FONT, 11),
        ).pack(fill="x", pady=(0, 14))

        tk.Label(
            outer,
            text="当前目标文件夹",
            font=(UI_FONT, 12, "bold"),
            anchor="w",
        ).pack(fill="x")

        folder_box = tk.Frame(outer, bg="#f2f2f2", padx=12, pady=12)
        folder_box.pack(fill="x", pady=(6, 10))

        tk.Label(
            folder_box,
            textvariable=self.folder_var,
            justify="left",
            anchor="w",
            wraplength=820,
            bg="#f2f2f2",
            font=(UI_FONT, 10),
        ).pack(fill="x")

        tk.Label(
            outer,
            text="原图回退目录（删图后移到这里）",
            font=(UI_FONT, 12, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        retry_box = tk.Frame(outer, bg="#f2f2f2", padx=12, pady=12)
        retry_box.pack(fill="x", pady=(6, 10))

        tk.Label(
            retry_box,
            textvariable=self.retry_var,
            justify="left",
            anchor="w",
            wraplength=820,
            bg="#f2f2f2",
            font=(UI_FONT, 10),
        ).pack(fill="x")

        actions = tk.Frame(outer, pady=6)
        actions.pack(fill="x")

        tk.Button(
            actions,
            text="使用当前文件夹",
            width=16,
            command=self.use_current_dir,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="选择文件夹",
            width=14,
            command=self.choose_dir,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="选择回退文件夹",
            width=16,
            command=self.choose_retry_dir,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="回退目录恢复默认",
            width=16,
            command=self.reset_retry_dir,
            font=(UI_FONT, 11),
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="开始查图",
            width=14,
            command=self.start_review,
            font=(UI_FONT, 11),
            bg="#2f6fda",
            fg="white",
        ).pack(side="left")

        tk.Label(
            outer,
            textvariable=self.status_var,
            justify="left",
            anchor="w",
            wraplength=840,
            fg="#9b1c1c",
            font=(UI_FONT, 10),
        ).pack(fill="x", pady=(16, 0))

        apply_dark_theme(self.root)
        self.refresh_status()

    def refresh_status(self) -> None:
        self.folder_var.set(str(self.selected_dir))
        self.retry_var.set(f"{self.selected_retry_dir}    （默认：{RETRY_ROOT_DIR}）")
        history_text = history_text_for(self.selected_dir)
        error = validate_folder(self.selected_dir)
        if error:
            status = f"当前还不能开始：{error}"
            if history_text:
                status += f"\n{history_text}"
            self.status_var.set(status)
            return

        match_count = count_parent_matches(self.selected_dir)
        if match_count == 0:
            status = "可以开始查图，但当前没发现上一层同名原图。I/W 还能用，D 删除时可能会提示找不到原图。"
        else:
            status = f"当前文件夹可用。已发现 {match_count} 张上一层同名原图。删图后原图会移到：{self.selected_retry_dir}"

        if history_text:
            status += f"\n{history_text}，点“开始查图”会从这里继续。"
        self.status_var.set(status)

    def use_current_dir(self) -> None:
        self.selected_dir = Path.cwd().resolve()
        save_launcher_history(self.selected_dir, self.selected_retry_dir)
        self.refresh_status()

    def choose_dir(self) -> None:
        chosen = filedialog.askdirectory(
            title="选择要查图的子文件夹",
            initialdir=str(self.selected_dir if self.selected_dir.exists() else Path.cwd()),
            mustexist=True,
        )
        if not chosen:
            return
        self.selected_dir = Path(chosen).resolve()
        save_launcher_history(self.selected_dir, self.selected_retry_dir)
        self.refresh_status()

    def choose_retry_dir(self) -> None:
        chosen = filedialog.askdirectory(
            title="选择原图回退目录",
            initialdir=str(self.selected_retry_dir if self.selected_retry_dir.exists() else RETRY_ROOT_DIR.parent),
            mustexist=False,
        )
        if not chosen:
            return
        self.selected_retry_dir = Path(chosen).resolve()
        save_launcher_history(self.selected_dir, self.selected_retry_dir)
        self.refresh_status()

    def reset_retry_dir(self) -> None:
        self.selected_retry_dir = RETRY_ROOT_DIR
        save_launcher_history(self.selected_dir, self.selected_retry_dir)
        self.refresh_status()

    def start_review(self) -> None:
        error = validate_folder(self.selected_dir)
        if error:
            messagebox.showwarning("还不能开始", error)
            return

        save_launcher_history(self.selected_dir, self.selected_retry_dir)
        self.start_paths = (self.selected_dir, self.selected_retry_dir)
        self.root.destroy()

    def run(self) -> tuple[Path, Path] | None:
        self.root.mainloop()
        return self.start_paths


def validate_folder(folder: Path) -> str | None:
    if not folder.exists():
        return f"目录不存在：{folder}"
    if not folder.is_dir():
        return f"不是文件夹：{folder}"

    images = list_images(folder)
    if not images:
        return "当前文件夹没有可处理图片。"
    return None


def main() -> int:
    initial_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    start_paths = LauncherApp(initial_dir).run()
    if start_paths is None:
        return 0

    start_dir, retry_dir = start_paths
    app = ReviewApp(start_dir, retry_dir)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
