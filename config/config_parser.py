from pathlib import Path

import yaml


def get_project_root(start_file: str | Path | None = None) -> Path:
    current = Path(start_file).resolve() if start_file else Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("未找到项目根目录（缺少 pyproject.toml）")


def load_config(start_file: str | Path | None = None) -> dict:
    project_root = get_project_root(start_file)
    config_path = project_root / "config" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"未找到配置文件: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def resolve_project_path(path_value: str | Path, start_file: str | Path | None = None) -> Path:
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (get_project_root(start_file) / path_obj).resolve()
