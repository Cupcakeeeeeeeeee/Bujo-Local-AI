import streamlit as st
import streamlit.components.v1 as components
import json
import base64
import os
import database.db_manager as db

STICKER_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "stickers")
COMP_DIR = os.path.join(os.path.dirname(__file__), "sticker_canvas_component")

# Declare component once at module level
_component_func = components.declare_component("sticker_canvas", path=COMP_DIR)

def load_all_svg_stickers():
    """Load all SVG stickers as base64 data URIs so they can be embedded cleanly into the HTML canvas."""
    stickers_data = {}
    if not os.path.exists(STICKER_DIR):
        return stickers_data

    for cat in os.listdir(STICKER_DIR):
        cat_path = os.path.join(STICKER_DIR, cat)
        if os.path.isdir(cat_path):
            stickers_data[cat] = {}
            for fname in os.listdir(cat_path):
                if fname.endswith(".svg"):
                    key = fname.replace(".svg", "")
                    fpath = os.path.join(cat_path, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        svg_content = f.read()
                    b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
                    data_uri = f"data:image/svg+xml;base64,{b64}"
                    stickers_data[cat][key] = data_uri
    return stickers_data

def render_sticker_canvas(date_str):
    """
    Renders an interactive Bullet Journal Dot-Grid notebook canvas with drag & drop,
    text stickers, SVG stickers, position tracking, and deletion.
    """
    stickers_dict = load_all_svg_stickers()
    existing_stickers = db.get_stickers_for_date(date_str)

    return _component_func(
        date_str=date_str,
        existing_stickers=existing_stickers,
        stickers_dict=stickers_dict,
        key=f"canvas_{date_str}"
    )
