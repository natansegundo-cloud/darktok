import shutil
from pathlib import Path

from studio.loader import ProjectLoader
from studio.session import session_items, write_session_sheet

ROOT = Path(__file__).parents[1]


def _copy_project(tmp_path: Path) -> Path:
    for directory in ("config", "styles", "templates"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copytree(
        ROOT / "series" / "revenge_republic",
        tmp_path / "series" / "revenge_republic",
    )
    return tmp_path


def test_session_filter_orders_images_before_videos_and_keeps_account(tmp_path: Path) -> None:
    root = _copy_project(tmp_path)
    bundle = ProjectLoader(root).load_episode_bundle("revenge_republic", "ep01")

    items = session_items(root, bundle, account="conta1")

    assert items
    assert [item.phase for item in items] == sorted(
        (item.phase for item in items), key=lambda phase: phase != "IMAGENS"
    )
    assert all(item.account in {"conta1", "—"} for item in items)
    assert any(item.phase == "IMAGENS" for item in items)
    assert any(item.phase == "VÍDEOS" for item in items)
    assert all(item.cost == 0 for item in items if item.phase == "IMAGENS")
    assert all(item.cost == 5 for item in items if item.phase == "VÍDEOS")


def test_session_sheet_contains_manual_steps_and_costs(tmp_path: Path) -> None:
    root = _copy_project(tmp_path)
    bundle = ProjectLoader(root).load_episode_bundle("revenge_republic", "ep01")

    target = write_session_sheet(root, bundle, account="conta1")
    content = target.read_text(encoding="utf-8")

    assert "IMAGENS" in content
    assert "VÍDEOS" in content
    assert "O que anexar" in content
    assert "P04" in content
    assert "5 créditos" in content
    assert "não acessa contas" in content
