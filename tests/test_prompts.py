from pathlib import Path

from studio.loader import ProjectLoader
from studio.models import DialogueLine
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
    assert "Leitura em português" in result.markdown
    assert "realista" not in result.prompt.lower() or "Contemporary realistic" in result.prompt


def test_validation_reports_videos_waiting_for_future_images() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    issues = validate_bundle(bundle)
    blocked = [issue for issue in issues if issue.level == "error"]
    assert {issue.shot_id for issue in blocked} == {"P04", "P05", "P06"}


def test_ten_second_video_uses_seven_credits() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P06")
    assert render_prompt(ROOT, bundle, shot.model_copy(update={"duration_s": 10})).cost == 7


def test_image_prompt_explains_reference_and_result() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P05i")
    result = render_prompt(ROOT, bundle, shot)
    assert "## IMAGEM:" in result.markdown
    assert "plano P03i" in result.markdown
    assert "Resultado esperado: Um close de dois personagens" in result.markdown
    assert "EP01_P05i_image.jpg" in result.markdown


def test_voice_over_is_rendered_and_intentional_silence_uses_expression_prompt() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P04")
    voice_over = shot.model_copy(
        update={
            "dialogue_pt": [],
            "voice_over_pt": [DialogueLine(speaker="duda", text="A prova ainda está comigo")],
        }
    )
    result = render_prompt(ROOT, bundle, voice_over)
    assert (
        'Voice-over of Duda, in Brazilian Portuguese (low, cold, controlled): '
        '"A prova ainda está comigo".'
        in result.prompt
    )
    assert "soft and sweet in public" not in result.prompt
    explicit = shot.model_copy(
        update={
            "dialogue_pt": [],
            "voice_over_pt": [
                DialogueLine(
                    speaker="duda",
                    text="A prova ainda está comigo",
                    delivery="whispered, controlled",
                    delivery_pt="sussurrada, controlada",
                )
            ],
        }
    )
    explicit_result = render_prompt(ROOT, bundle, explicit)
    assert (
        "Voice-over of Duda, in Brazilian Portuguese (whispered, controlled)"
        in explicit_result.prompt
    )
    silent = shot.model_copy(update={"dialogue_pt": [], "intentional_silence": True})
    silent_result = render_prompt(ROOT, bundle, silent)
    assert "No dialogue, mouth closed" in silent_result.prompt


def test_style_rules_and_negative_hints_enter_image_prompt() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P05i")
    result = render_prompt(ROOT, bundle, shot)
    assert "realistic features" in result.prompt
    assert "no watermark" in result.prompt


def test_missing_portuguese_prompt_field_is_explicit() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P04i")
    result = render_prompt(ROOT, bundle, shot.model_copy(update={"framing_pt": ""}))
    assert "[falta tradução: campo framing]" in result.prompt_pt


def test_video_prompt_contains_timed_direction_and_constraints() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P03")
    result = render_prompt(ROOT, bundle, shot)
    assert "Scene setup:" in result.prompt
    assert "At 0-2s:" in result.prompt
    assert "Do not:" in result.prompt
    assert "Direção por tempo:" in result.prompt_pt
    assert "Não fazer:" in result.prompt_pt
