import argparse
import json
import os
import re

# Regexes to match the start of a document
DOCUMENT = r"^.*?DEPARTMENT OF DEFENSE APPROPRIATIONS FOR (\d+)$"

# Regexes to parse the subcommittee members.
COMMITTEE_BEGIN = r".*SUBCOMMITTEE ON.*"
COMMITTEE_MEMBERS = r"(?:^\s|\b)\s+?([^,]*?),+?([^,]*?),*?([^,]*?)(?=\t|\n)"
COMMITTEE_END = r"^\s+NOTE:"

# Regexes to parse a hearing.
HEARING = r"^\s+?(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\w+,\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w+\s\d+,\s\d+\.$"

# Regexes to parse the witnesses.
WITNESS_BEGIN = r"^\s+WITNESS\w*$"
WITNESSES = r"^([^,]+?),(.+?)(?=\n)"
WITNESS_END = r"^\s{8,}"

# Regexes to parse the speakers.
SPEAKER = r"^\s{4,}([A-Z][\w-]+)\.?\s([A-Z][\w\s-]+)\s?(\[\w+\])?\.(.+)$"
TITLE = r"^\s+([^a-z]{2,})$"


def main() -> None:
    """Main function"""

    args = parse_cli_args()

    if os.path.isdir(args.input):
        for file in os.listdir(args.input):
            if file.endswith(".txt"):
                output = parse_document(os.path.join(args.input, file))
                save_output(os.path.join(args.output, file.replace(".txt", ".json")), output)
    else:
        output = parse_document(args.input)
        save_output(args.output, output)


def parse_cli_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """

    parser = argparse.ArgumentParser(description="HAC-D hearing transcript parser")

    parser.add_argument(
        "-i", "--input", dest="input", required=True, help="Path to input file"
    )

    parser.add_argument(
        "-o", "--output", dest="output", required=True, help="Path to output file"
    )

    return parser.parse_args()


def parse_document(path: str) -> dict:
    """
    Parse the input file.

    Args:
        path (str): The path of the file to parse.

    Returns:
        dict: The parsed data.
    """

    output = {
        "header": {},
        "members": [],
        "hearings": [{}],
    }

    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        state = "START"
        line = file.readline()

        while line:
            if state == "START":
                match = re.match(DOCUMENT, line)
                if match:
                    output["header"]["year"] = match.group(1)
                    state = "DOCUMENT"

            elif state == "DOCUMENT":
                committee = re.match(COMMITTEE_BEGIN, line)
                hearing = re.match(HEARING, line)

                if committee:
                    state = "COMMITTEE"
                elif hearing:
                    state = "HEARING"
                    output["hearings"][-1]["date"] = line.strip()

            elif state == "COMMITTEE":
                if re.match(COMMITTEE_END, line):
                    state = "DOCUMENT"
                else:
                    group = filter(None, re.split("(?:\s{2,}|\t{2,})", line.strip()))
                    for member in group:
                        tokens = member.split(",")
                        if "Chair" in tokens[-1]:
                            output["members"].append({
                                "name": tokens[0].strip(),
                                "district": tokens[-2].strip(),
                            })
                        else:
                            output["members"].append({
                                "name": tokens[0].strip(),
                                "district": tokens[-1].strip(),
                            })
                        
            elif state == "HEARING":
                if re.match(WITNESS_BEGIN, line):
                    state = "WITNESSES"

            elif state == "WITNESSES":
                if re.match(WITNESS_END, line):
                    state = "CONTENT"
                elif line.strip():
                    value = output["hearings"][-1].get("witnesses", [])
                    output["hearings"][-1]["witnesses"] = value + [line.strip()]

            elif state == "CONTENT":
                speaker = re.match(SPEAKER, line)
                hearing = re.match(HEARING, line)

                if hearing:
                    state = "HEARING"
                    output["hearings"].append({})
                    output["hearings"][-1]["date"] = line.strip()
                elif speaker:
                    state = "SPEAKER"
                    value = output["hearings"][-1].get("speakers", [])
                    output["hearings"][-1]["speakers"] = value + [{
                        "title": speaker.group(1),
                        "surname": speaker.group(2),
                        "remarks": speaker.group(4).strip(),
                    }]
            
            elif state == "SPEAKER":
                speaker = re.match(SPEAKER, line)

                if not line.strip():
                    state = "CONTENT" 
                elif speaker:
                    value = output["hearings"][-1].get("speakers", [])
                    output["hearings"][-1]["speakers"] = value + [{
                        "title": speaker.group(1),
                        "surname": speaker.group(2),
                        "remarks": speaker.group(4).strip(),
                    }]
                else:
                    if output["hearings"][-1].get("speakers"):
                        remarks = output["hearings"][-1]["speakers"][-1].get("remarks", "")
                        output["hearings"][-1]["speakers"][-1]["remarks"] = " ".join([remarks, line.strip()])

            line = file.readline()

        return output



def save_output(path: str, output: dict) -> None:
    """
    Save the output to a file.

    Args:
        path (str): The path to the file to save to.
        output (dict): The output to save.
    """

    with open(path, "w") as file:
        json.dump(output, file, indent=4)


if __name__ == "__main__":
    main()
