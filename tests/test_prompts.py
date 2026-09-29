from pathlib import Path

from studio.loader import ProjectLoader
from studio.prompts import render_prompt, validate_bundle

ROOT = Path(__file__).parents[1]


def test_video_prompt_keeps_lock_blocks_and_dialogue_order() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P02")
    result = render_prompt(ROOT, bundle, shot)
    assert "Animate the attached image." in result.prompt
    assert "Manu, 20-year-old Brazilian woman" in result.prompt or "Duda" in result.prompt
    assert 'First Duda says' in result.prompt
    assert 'Then Manu says' in result.prompt
    assert result.cost == 6
    assert "## VIDEO:" in result.markdown
    assert "Anexar a imagem aprovada do plano P02i" in result.markdown
    assert "Resultado esperado: As duas permanecem na cozinha" in result.markdown


def test_validation_reports_videos_waiting_for_future_images() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    issues = validate_bundle(bundle)
    blocked = [issue for issue in issues if issue.level == "error"]
    assert {issue.shot_id for issue in blocked} == {"P04", "P05", "P06"}


def test_ten_second_video_uses_seven_credits() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P06")
    assert render_prompt(ROOT, bundle, shot).cost == 7


def test_image_prompt_explains_reference_and_result() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P05i")
    result = render_prompt(ROOT, bundle, shot)
    assert "## IMAGEM:" in result.markdown
    assert "plano P03i" in result.markdown
    assert "Resultado esperado: Um close de dois personagens" in result.markdown
    assert "EP01_P05i_image.jpg" in result.markdown
