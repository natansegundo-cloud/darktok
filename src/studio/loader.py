from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import load_production, read_yaml
from .models import (
    CharactersFile,
    Episode,
    LocationsFile,
    Series,
    ShotsFile,
    StylePreset,
)


@dataclass(frozen=True)
class LoadedEpisode:
    series: Series
    characters: CharactersFile
    locations: LocationsFile
    style: StylePreset
    episode: Episode
    shots: ShotsFile
    series_dir: Path
    episode_dir: Path
    profile_name: str = ""


class ProjectLoader:
    def __init__(self, root: Path):
        self.root = root

    def series_dir(self, series_id: str) -> Path:
        return self.root / "series" / series_id

    def episode_dir(self, series_id: str, episode_id: str) -> Path:
        return self.series_dir(series_id) / "episodes" / episode_id

    def load_series(self, series_id: str) -> Series:
        path = self.series_dir(series_id) / "series.yaml"
        return Series.model_validate(read_yaml(path))

    def load_characters(self, series_id: str) -> CharactersFile:
        path = self.series_dir(series_id) / "characters.yaml"
        return CharactersFile.model_validate(read_yaml(path))

    def load_locations(self, series_id: str) -> LocationsFile:
        path = self.series_dir(series_id) / "locations.yaml"
        return LocationsFile.model_validate(read_yaml(path))

    def load_style(self, series: Series) -> StylePreset:
        path = self.root / "styles" / f"{series.style}.yaml"
        return StylePreset.model_validate(read_yaml(path))

    def load_episode(self, series_id: str, episode_id: str) -> Episode:
        path = self.episode_dir(series_id, episode_id) / "episode.yaml"
        return Episode.model_validate(read_yaml(path))

    def load_shots(self, series_id: str, episode_id: str) -> ShotsFile:
        path = self.episode_dir(series_id, episode_id) / "shots.yaml"
        return ShotsFile.model_validate(read_yaml(path))

    def load_episode_bundle(self, series_id: str, episode_id: str) -> LoadedEpisode:
        series = self.load_series(series_id)
        series_dir = self.series_dir(series_id)
        episode_dir = self.episode_dir(series_id, episode_id)
        episode = self.load_episode(series_id, episode_id)
        production = load_production(self.root)
        profile_name = production.effective_profile_name(series.profile, episode.profile)
        return LoadedEpisode(
            series=series,
            characters=self.load_characters(series_id),
            locations=self.load_locations(series_id),
            style=self.load_style(series),
            episode=episode,
            shots=self.load_shots(series_id, episode_id),
            series_dir=series_dir,
            episode_dir=episode_dir,
            profile_name=profile_name,
        )
