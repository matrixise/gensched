import argparse
import pathlib

import frontmatter
import prettyprinter

# from prettytable import PrettyTable
import datetime
import tabulate
import humanize

# import pretty_errors

# better_exceptions.MAX_LENGTH = None
from gensched.models import ConfigurationModel, ChapterModel, SectionModel

HOURS_PER_DAY = datetime.timedelta(hours=8)
HOURS_PER_DAY_IN_SECONDS = int(HOURS_PER_DAY.total_seconds())

DAYS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri"}


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Schedule directory",
        type=lambda p: pathlib.Path(p).absolute().resolve(),
        default=pathlib.Path(__file__).absolute().parent / "schedule",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    configuration = ConfigurationModel.load(args.directory.joinpath("config.yml"))

    prettyprinter.cpprint(configuration)

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

    # table = PrettyTable()
    # table.field_names = [
    #     "Day",
    #     "Chapter",
    #     "Section",
    #     "Duration",
    #     "Splitted Duration",
    # ]

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

            rows.append(
                [
                    DAYS[(day % len(DAYS)) + 1],
                    section.chapter.name,
                    section.name,
                    # current_duration,
                    humanize.precisedelta(current_duration),
                    humanize.precisedelta(
                        datetime.timedelta(seconds=duration_in_seconds)
                    ),
                ]
            )
            current_duration_in_seconds -= duration_in_seconds
            total_duration_training_seconds += duration_in_seconds
            if total_duration_in_seconds >= HOURS_PER_DAY_IN_SECONDS:
                total_duration_in_seconds = 0
                day += 1

    table = tabulate.tabulate(
        rows,
        headers=["Day", "Chapter", "Section", "Duration", "Splitted Duration"],
        tablefmt="pretty",
    )
    print(table)
    # print(
    #     humanize.abs_timedelta(
    #         datetime.timedelta(seconds=total_duration_training_seconds)
    #     )
    # )


if __name__ == "__main__":
    main()
