import argparse
import pathlib

import prettyprinter
import tabulate

from gensched.gensched import get_sections, build_rows
from gensched.models import ConfigurationModel


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

    sections = get_sections(args, configuration)

    rows = build_rows(sections)

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
