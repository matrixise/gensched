import datetime
import enum
import pathlib
import typing

import frontmatter
import pydantic
import pydantic_yaml
import pytimeparse


class LevelEnum(enum.Enum):
    STARTER = "starter"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class IdMixin(pydantic.BaseModel):
    id: str


class NameMixin(pydantic.BaseModel):
    name: str


class TagsMixin(pydantic.BaseModel):
    tags: typing.Optional[typing.List[str]] = pydantic.Field(default_factory=list)


def parse_frontmatter(path: pathlib.Path, defaults=None):
    with path.open() as fp:
        if defaults is None:
            defaults = {}
        return frontmatter.parse(fp.read(), **defaults)


class PathLoaderMixin:
    @classmethod
    def load(cls, path: pathlib.Path, **kwargs):
        metadata, content = parse_frontmatter(path)
        if kwargs:
            metadata.update(kwargs)
        return cls(**metadata), content


class ConfigurationModel(pydantic_yaml.YamlModel):
    name: str
    duration: str = "1h"
    project: typing.Optional[str] = None
    version: typing.Optional[float] = None
    level: LevelEnum = LevelEnum.STARTER
    dependencies: typing.Optional[typing.List[str]]
    chapters: typing.List[str]
    requirements: typing.Dict[str, typing.List[str]]

    @classmethod
    def load(cls, configuration_file: pathlib.Path):
        with configuration_file.open() as fp:
            return ConfigurationModel.parse_raw(fp, proto="yaml")


class ChapterModel(IdMixin, NameMixin, TagsMixin, PathLoaderMixin, pydantic.BaseModel):
    sections: typing.Optional[typing.List[str]] = pydantic.Field(default_factory=list)

    @property
    def slug(self):
        return self.id


class SectionModel(IdMixin, NameMixin, TagsMixin, pydantic.BaseModel):
    chapter: ChapterModel
    duration: datetime.timedelta

    @property
    def slug(self):
        return f"{self.chapter.slug}_{self.id}"

    @classmethod
    def load(cls, path: pathlib.Path, id: str, chapter: ChapterModel):
        metadata, content = parse_frontmatter(
            path,
            defaults=dict(duration="1h", name=map(str.title, path.name.split("_"))),
        )

        metadata["id"] = id
        metadata["chapter"] = chapter
        metadata["duration"] = pytimeparse.parse(str(metadata["duration"]))
        return cls(**metadata), content
