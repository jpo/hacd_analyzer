import argparse
import json
import pandas as pd
from textblob import TextBlob


# Speaker rate in words per minute.
WPM = 140


def main() -> None:
    """Main function"""

    args = parse_cli_args()
    output = analyze(args.input)
    save_output(args.output, output)


def parse_cli_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """

    parser = argparse.ArgumentParser(description="HAC-D analysis script")

    parser.add_argument(
        "-i", "--input", dest="input", required=True, help="Path to input file"
    )

    parser.add_argument(
        "-o", "--output", dest="output", required=True, help="Path to output file(s)"
    )

    return parser.parse_args()


def analyze(path: str) -> pd.DataFrame:
    """
    Analyze the input file.

    Args:
        path (str): The path of the file to analyze.

    Returns:
    """

    with open(path, "r") as file:
        data = json.load(file)
        df_members = pd.DataFrame(data["members"])
        df_witnesses = pd.DataFrame(data["witnesses"])
        df_content = pd.DataFrame(data["content"])

        df_content["role"] = df_content.speaker_surname.apply(
            lambda s: "WITNESS" if df_witnesses.name.str.contains(s).any() else "MEMBER"
        )

        df_content["district"] = df_content.speaker_surname.apply(
            lambda s: df_members[df_members.name.str.contains(s)].district.values[0] \
                if df_members.name.str.contains(s).any() else None
        )

        df_content["minutes"] = df_content.word_count / WPM

        df_content["polarity"], df_content["subjectivity"] = zip(
            *df_content.remarks.map(lambda r: TextBlob(r).sentiment)
        )

        df_content = df_content.reindex(columns=[
            "topic_id",
            "topic_name",
            "speaker_title",
            "speaker_surname",
            "speaker_name",
            "district",
            "role",
            "word_count",
            "question_count",
            "minutes",
            "polarity",
            "subjectivity",
            "remark_id",
            "remarks",
        ])

        return df_content


def save_output(path: str, output: pd.DataFrame) -> None:
    """
    Save the output to a file.

    Args:
        path (str): The path to the file to save to.
        output (pd.DataFrame): The output to save.
    """

    output.to_csv(path, index=False)


if __name__ == "__main__":
    main()
