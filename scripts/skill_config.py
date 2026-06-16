#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Any, Dict


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def _load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"").strip("'")
    return values


def _build_env_overrides(env: Dict[str, str]) -> Dict[str, Any]:
    canvas_width = env.get("JIANYING_CANVAS_WIDTH", "").strip()
    canvas_height = env.get("JIANYING_CANVAS_HEIGHT", "").strip()
    image_scale_x = env.get("JIANYING_IMAGE_SCALE_X", "").strip()
    image_scale_y = env.get("JIANYING_IMAGE_SCALE_Y", "").strip()
    image_transform_x = env.get("JIANYING_IMAGE_TRANSFORM_X", "").strip()
    image_transform_y = env.get("JIANYING_IMAGE_TRANSFORM_Y", "").strip()

    cfg: Dict[str, Any] = {
        "draft_parent_folder": env.get("JIANYING_DRAFT_PARENT_FOLDER", "").strip(),
        "subtitle_style_sample_draft": env.get("JIANYING_SUBTITLE_STYLE_SAMPLE_DRAFT", "").strip(),
        "default_template_id": env.get("JIANYING_DEFAULT_TEMPLATE_ID", "").strip(),
        "servicehub": {
            "base_url": env.get("SERVICETUBER_BASE_URL", "").strip(),
            "username": env.get("SERVICETUBER_USERNAME", "").strip(),
            "passtoken": env.get("SERVICETUBER_PASSTOKEN", "").strip(),
            "asr_provider": env.get("JIANYING_ASR_PROVIDER", "").strip(),
            "asr_model": env.get("JIANYING_ASR_MODEL", "").strip(),
            "llm_provider": env.get("JIANYING_LLM_PROVIDER", "").strip(),
            "llm_model": env.get("JIANYING_LLM_MODEL", "").strip(),
        },
        "canvas": {},
        "image_style": {},
    }

    if canvas_width:
        cfg["canvas"]["width"] = int(canvas_width)
    if canvas_height:
        cfg["canvas"]["height"] = int(canvas_height)
    if image_scale_x:
        cfg["image_style"]["scale_x"] = float(image_scale_x)
    if image_scale_y:
        cfg["image_style"]["scale_y"] = float(image_scale_y)
    if image_transform_x:
        cfg["image_style"]["transform_x"] = float(image_transform_x)
    if image_transform_y:
        cfg["image_style"]["transform_y"] = float(image_transform_y)
    return cfg


def _clean_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {k: _clean_empty(v) for k, v in value.items()}
        return {k: v for k, v in cleaned.items() if v not in ("", None, {}, [])}
    if isinstance(value, list):
        cleaned = [_clean_empty(v) for v in value]
        return [v for v in cleaned if v not in ("", None, {}, [])]
    return value


def load_runtime_config(project_root: Path, config_path: Path | None = None) -> Dict[str, Any]:
    root = Path(project_root).resolve()
    base_config = _load_json_file(root / "config.json")
    if config_path:
        override_config = _load_json_file(Path(config_path).resolve())
        base_config = _deep_merge_dict(base_config, override_config)

    env_file = _load_env_file(root / ".env")
    combined_env = dict(env_file)
    combined_env.update({k: v for k, v in os.environ.items() if isinstance(v, str)})

    local_credentials = _load_json_file(root / "data" / "credentials.json")
    merged = _deep_merge_dict(base_config, local_credentials)
    env_overrides = _clean_empty(_build_env_overrides(combined_env))
    merged = _deep_merge_dict(merged, env_overrides)
    return merged
