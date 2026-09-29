from pathlib import Path

from studio.board import board_rows, next_row, render_board
from studio.loader import ProjectLoader

ROOT = Path(__file__).parents[1]


def test_board_links_video_to_parent_image() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    row = next(item for item in board_rows(bundle) if item.shot_id == "P03")
    assert row.stage == "VIDEO"
    assert "EP01_P03i_image.jpg" in row.source_image
    assert "P03.md" in row.prompt_file
    assert row.summary_pt


def test_board_makes_missing_media_visible() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    board = render_board(bundle)
    assert "MISSING" in board
    assert "P03i" in board
    assert "Resumos em português" in board
    assert "Perfil: growth (360p)" in board


def test_next_blocks_video_until_parent_image_file_exists() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    row = next_row(bundle)
    assert row is not None
    assert "Colocar imagem" in row.next_action or "Gerar imagem" in row.next_action
