import argparse
import json
import os
import pandas as pd
from textblob import TextBlob


def main() -> None:
    """Main function"""

    args = parse_cli_args()

    if os.path.isdir(args.input):
        for file in os.listdir(args.input):
            if file.endswith(".json"):
                print(file)
                output = analyze(os.path.join(args.input, file))
                save_output(os.path.join(args.output, file.replace(".json", ".csv")), output)
    else:
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
        hearings = data["hearings"]
        df_members = pd.DataFrame(data.get("members", []), columns=["name", "district"])
        output = []

        for hearing in hearings:
            if "witnesses" not in hearing or "speakers" not in hearing:
                continue

            df_witnesses = pd.DataFrame(data=hearing.get("witnesses", []), columns=["name"])

            df_speakers = pd.DataFrame(hearing.get("speakers", []))
            df_speakers["year"] = data["header"]["year"]
            df_speakers["date"] = hearing["date"]

            df_speakers["role"] = df_speakers.surname.apply(
                lambda s: "WITNESS" if df_witnesses.name.str.contains(s.upper()).any() else "MEMBER"
            )

            df_speakers["district"] = df_speakers.surname.apply(
                lambda s: df_members[df_members.name.str.contains(s.upper())].district.values[0] \
                    if df_members.name.str.contains(s.upper()).any() else None
            )

            df_speakers["district_mentions"] = df_speakers.remarks.apply(
                lambda r: r.count("my district") \
                    + r.count("my state") \
                    + r.count("my constituents") \
                    + r.count("I represent")) 

            df_speakers["word_count"] = df_speakers.remarks.apply(lambda r: len(r.split()))

            df_speakers["question_count"] = df_speakers.remarks.apply(lambda r: r.count("?"))

            df_speakers["polarity"], df_speakers["subjectivity"] = zip(
                *df_speakers.remarks.map(lambda r: TextBlob(r).sentiment)
            )

            df_speakers = df_speakers.reindex(columns=[
                "year",
                "date",
                "title",
                "surname",
                "role",
                "district",
                "district_mentions",
                "word_count",
                "question_count",
                "polarity",
                "subjectivity",
                "remarks",
            ])

            output.append(df_speakers)

        return pd.concat(output, ignore_index=True)


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
