from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StudioModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Nickname(StudioModel):
    name: str
    used_by: list[str] = Field(default_factory=list)


class Character(StudioModel):
    id: str
    name: str
    full_name: str | None = None
    nicknames: list[Nickname] = Field(default_factory=list)
    role: Literal["protagonist", "villain", "ally", "love_interest", "support"] = "support"
    age: int | None = None
    lock_version: int = 1
    lock_block: str
    signature_element: str | None = None
    hair_color: str | None = None
    voice_notes: str = ""
    bio_pt: str = ""
    arc_pt: str = ""
    approved_reference: str | None = None


class CharactersFile(StudioModel):
    characters: list[Character] = Field(default_factory=list)


class Location(StudioModel):
    id: str
    name: str = ""
    description_en: str
    default_light: str = "natural light"


class LocationsFile(StudioModel):
    locations: list[Location] = Field(default_factory=list)


class StylePreset(StudioModel):
    id: str
    name: str
    style_block: str
    negative_hints: str = ""
    camera_defaults: str = ""
    video_motion_defaults: str = "subtle natural motion"
    notes: str = ""
    character_rules: str = ""


class Series(StudioModel):
    id: str
    title: str
    genre: str = ""
    audience: str = ""
    language: str = "pt-BR"
    aspect_ratio: str = "9:16"
    style: str
    episodes_planned: int = 1
    episode_target_seconds: list[int] = Field(default_factory=lambda: [30, 90])
    logline: str = ""
    synopsis: str = ""
    season_hook: str = ""
    status: Literal["idea", "planning", "in_production", "paused", "released"] = "planning"


class ColdOpen(StudioModel):
    enabled: bool = False
    source_shot: str | None = None
    trim_start_s: float = 0.0
    trim_end_s: float = 3.5
    transition: str = "white flash + impact sound"
    title_card_pt: str = "Horas antes..."


class Episode(StudioModel):
    id: str
    title: str
    number: int
    target_seconds: int = 60
    cold_open: ColdOpen = Field(default_factory=ColdOpen)
    cliffhanger: str = ""
    key_prop: str = ""
    status: Literal[
        "planning", "scripted", "prompts_ready", "generating", "editing", "ready", "posted"
    ] = "planning"
    metrics: dict[str, object] = Field(default_factory=dict)
    notes: str = ""


class DialogueLine(StudioModel):
    speaker: str
    text: str


class ShotFiles(StudioModel):
    image: str | None = None
    video: str | None = None


class Shot(StudioModel):
    id: str
    order: int
    kind: Literal["anchor_image", "derived_image", "video_from_image", "video_expression_only"]
    role: Literal["hook", "body", "cliffhanger"] = "body"
    location: str
    characters: list[str] = Field(default_factory=list)
    framing: str = "medium shot"
    action: str = ""
    action_en: str = ""
    expected_result_pt: str = ""
    camera: str = ""
    gaze: str = ""
    mood: str = ""
    expression: str = ""
    parent: str | None = None
    reference_from: str | None = None
    light: str | None = None
    dialogue_pt: list[DialogueLine] = Field(default_factory=list)
    voice_mode: Literal["native"] = "native"
    duration_s: int = 8
    account: str | None = None
    status: Literal["todo", "prompt_ready", "generated", "approved", "rejected", "edited"] = "todo"
    video_attempts: int = 0
    files: ShotFiles = Field(default_factory=ShotFiles)
    notes: str = ""


class ShotsFile(StudioModel):
    shots: list[Shot] = Field(default_factory=list)


class VideoConfig(StudioModel):
    resolution: str = "360p"
    default_duration_s: int = 8
    duration_credits: dict[int, int] = Field(default_factory=lambda: {6: 5, 8: 6, 10: 7})
    max_attempts: int = 2


class ImageConfig(StudioModel):
    credits: int = 0


class AccountsConfig(StudioModel):
    count: int = 5
    daily_credits_per_account: int = 50
    reserve_videos_per_account: int = 1


class WorkflowConfig(StudioModel):
    mode: Literal["images_first", "sequential"] = "images_first"


class ProductionConfig(StudioModel):
    tool: str = "google_flow"
    aspect_ratio: str = "9:16"
    video: VideoConfig = Field(default_factory=VideoConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    accounts: AccountsConfig = Field(default_factory=AccountsConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)

    def video_credits(self, duration_s: int) -> int:
        try:
            return self.video.duration_credits[duration_s]
        except KeyError as exc:
            supported = ", ".join(str(value) for value in sorted(self.video.duration_credits))
            raise ValueError(f"Unsupported video duration {duration_s}s; use: {supported}") from exc

    def shot_credits(self, shot: Shot) -> int:
        if shot.kind in {"anchor_image", "derived_image"}:
            return self.image.credits
        return self.video_credits(shot.duration_s)


class Account(StudioModel):
    id: str


class AccountsFile(StudioModel):
    accounts: list[Account] = Field(default_factory=list)


class ValidationIssue(StudioModel):
    level: Literal["error", "warning"]
    message: str
    shot_id: str | None = None
