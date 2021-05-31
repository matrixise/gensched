import datetime

import humanize

from gensched.models import ChapterModel, SectionModel

HOURS_PER_DAY = datetime.timedelta(hours=8)
HOURS_PER_DAY_IN_SECONDS = int(HOURS_PER_DAY.total_seconds())

DAYS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri"}


def build_rows(sections):
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

            total_duration_in_seconds += duration_in_seconds

            yield build_row(current_duration, day, duration_in_seconds, section)

            current_duration_in_seconds -= duration_in_seconds
            total_duration_training_seconds += duration_in_seconds
            if total_duration_in_seconds >= HOURS_PER_DAY_IN_SECONDS:
                total_duration_in_seconds = 0
                day += 1
    return rows


def build_row(current_duration, day, duration_in_seconds, section):
    return [
        DAYS[(day % len(DAYS)) + 1],
        section.chapter.name,
        section.name,
        humanize.precisedelta(current_duration),
        humanize.precisedelta(
            datetime.timedelta(seconds=duration_in_seconds)
        ),
    ]


def get_sections(args, configuration):
    sections = []
    for chapter_name in configuration.chapters:
        path = args.directory.joinpath(chapter_name, "index.md")
        if not path.exists():
            # print(f"Chapter - {chapter_name} does not exist")
            continue
        chapter, chapter_content = ChapterModel.load(path, id=chapter_name)
        # prettyprinter.cpprint(chapter)
        for section_name in chapter.sections:
            path = args.directory.joinpath(chapter_name).joinpath(section_name + ".md")
            # if not path.exists():
            #     # print(f"Section - {path} does not exist")
            #     continue
            # print(f"Section - {path}")
            section, section_content = SectionModel.load(
                path=path, id=section_name, chapter=chapter
            )

            sections.append(section)
    return sections
