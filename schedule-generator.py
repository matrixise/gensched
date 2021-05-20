import pathlib
import typing

import frontmatter
import prettyprinter
import pydantic
import pydantic_yaml

HOURS_PER_DAY = 8.0

class ConfigurationModel(pydantic_yaml.YamlModel):
    name: str
    days: int = 1
    project: typing.Optional[str] = None
    version: typing.Optional[float] = None
    level: str = 'beginner'
    dependencies: typing.Optional[typing.List[str]]
    chapters: typing.List[str]
    requirements: typing.Dict[str, typing.List[str]]

    @classmethod
    def load(cls, configuration_file: str):
        with pathlib.Path(configuration_file).open() as fp:
            return ConfigurationModel.parse_raw(fp, proto='yaml')

class PathLoaderMixin:
    @classmethod
    def load(cls, path: pathlib.Path):
        with path.open() as fp:
            metadata, content = frontmatter.parse(fp.read())
        return cls(**metadata), content

class NameMixin(pydantic.BaseModel):
    name: str

class TagsMixin(pydantic.BaseModel):
    tags: typing.Optional[typing.List[str]] = pydantic.Field(default_factory=list)

class ChapterModel(NameMixin, TagsMixin, PathLoaderMixin, pydantic.BaseModel):
    sections: typing.Optional[typing.List[str]] = pydantic.Field(default_factory=list)

class SectionModel(NameMixin, TagsMixin, PathLoaderMixin, pydantic.BaseModel):
    duration: typing.Optional[int] = 25

def main():
    # from devtools import debug
    configuration = ConfigurationModel.load('config.yml')
    # debug(configuration)
    prettyprinter.cpprint(configuration)

    for part_name in configuration.chapters:
        index_md = pathlib.Path.cwd().joinpath(part_name, 'index.md')
        if not index_md.exists():
            print(f'Chapter - {part_name} does not exist')
            continue
        part, part_content = ChapterModel.load(index_md)
        prettyprinter.cpprint(part)
        for item in part.sections:
            path = pathlib.Path(part_name).joinpath(item + '.md')
            if not path.exists():
                print(f'Section - {path} does not exist')
                continue
            item_part, item_part_content = SectionModel.load(path)
            prettyprinter.cpprint(item_part)

if __name__ == '__main__':
    main()