import collections
import enum
from functools import total_ordering
import pathlib
import typing

import frontmatter
import prettyprinter
import pydantic
import pydantic_yaml
import pytimeparse
from prettytable import PrettyTable
import datetime
import humanize
# import pretty_errors
import better_exceptions

# better_exceptions.MAX_LENGTH = None


HOURS_PER_DAY = datetime.timedelta(hours=8)
HOURS_PER_DAY_IN_SECONDS = int(HOURS_PER_DAY.total_seconds())

print(HOURS_PER_DAY, HOURS_PER_DAY_IN_SECONDS)


DAYS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri"}


class LevelEnum(enum.Enum):
    STARTER = "starter"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


def parse_frontmatter(path: pathlib.Path, defaults=None):
    with path.open() as fp:
        if defaults is None:
            defaults = {}
        return frontmatter.parse(fp.read(), **defaults)


class ConfigurationModel(pydantic_yaml.YamlModel):
    name: str
    duration: str = '1h'
    project: typing.Optional[str] = None
    version: typing.Optional[float] = None
    level: LevelEnum = LevelEnum.STARTER
    dependencies: typing.Optional[typing.List[str]]
    chapters: typing.List[str]
    requirements: typing.Dict[str, typing.List[str]]

    @classmethod
    def load(cls, configuration_file: str):
        with pathlib.Path(configuration_file).open() as fp:
            return ConfigurationModel.parse_raw(fp, proto="yaml")


class PathLoaderMixin:
    @classmethod
    def load(cls, path: pathlib.Path, **kwargs):
        metadata, content = parse_frontmatter(path)
        if kwargs:
            metadata.update(kwargs)
        return cls(**metadata), content


class IdMixin(pydantic.BaseModel):
    id: str


class NameMixin(pydantic.BaseModel):
    name: str


class TagsMixin(pydantic.BaseModel):
    tags: typing.Optional[typing.List[str]] = pydantic.Field(default_factory=list)


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
        metadata, content = parse_frontmatter(path, defaults=dict(duration='1h', name=map(str.title, path.name.split('_'))))

        metadata["id"] = id
        metadata["chapter"] = chapter
        metadata["duration"] = pytimeparse.parse(str(metadata["duration"]))
        return cls(**metadata), content


def main():
    configuration = ConfigurationModel.load("config.yml")
    # prettyprinter.cpprint(configuration)

    sections = []

    for chapter_name in configuration.chapters:
        path = pathlib.Path.cwd().joinpath(chapter_name, "index.md")
        if not path.exists():
            # print(f"Chapter - {chapter_name} does not exist")
            continue
        chapter, chapter_content = ChapterModel.load(path, id=chapter_name)
        # prettyprinter.cpprint(chapter)
        for section_name in chapter.sections:
            path = pathlib.Path(chapter_name).joinpath(section_name + ".md")
            # if not path.exists():
            #     # print(f"Section - {path} does not exist")
            #     continue
            # print(f"Section - {path}")
            section, section_content = SectionModel.load(
                path=path, id=section_name, chapter=chapter
            )
            print(section)

            sections.append(section)
            # prettyprinter.cpprint(section)

    # prettyprinter.cpprint(sections)
    table = PrettyTable()
    table.field_names = [
        "Day",
        "Chapter",
        "Section",
        # "Duration",
        # "Splitted Duration",
    ]

    total_duration_in_seconds = 0

    total_duration_training_seconds = 0

    rows = []
    day = 0

    for section in sections:
        current_duration = section.duration

        current_duration_in_seconds = int(current_duration.total_seconds())
        while current_duration_in_seconds > 0:
            available_in_seconds = HOURS_PER_DAY_IN_SECONDS - total_duration_in_seconds

            duration_in_seconds = min(current_duration_in_seconds, available_in_seconds)
            # if current_duration_in_seconds <= available_in_seconds:
            #     duration_in_seconds = current_duration_in_seconds
            # else:
            #     duration_in_seconds = available_in_seconds

            total_duration_in_seconds += duration_in_seconds

            rows.append(
                [
                    DAYS[(day % len(DAYS)) + 1],
                    section.chapter.name,
                    section.name,
                    # humanize.precisedelta(current_duration),
                    # humanize.precisedelta(
                    #     datetime.timedelta(seconds=duration_in_seconds)
                    # ),
                ]
            )
            current_duration_in_seconds -= duration_in_seconds
            total_duration_training_seconds += duration_in_seconds
            if total_duration_in_seconds >= HOURS_PER_DAY_IN_SECONDS:
                total_duration_in_seconds = 0
                day += 1

    table.add_rows(rows)
    print(table)
    # print(
    #     humanize.abs_timedelta(
    #         datetime.timedelta(seconds=total_duration_training_seconds)
    #     )
    # )


if __name__ == "__main__":
    main()
