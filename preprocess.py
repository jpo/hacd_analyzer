import argparse
import json
import re

from io import StringIO

RE_COMMITTEE_BEGIN = r"^\s+SUBCOMMITTEE ON DEFENSE$"
RE_COMMITTEE_MEMBERS = r"(?:^\s|\b)\s+?([^,]*?),+?([^,]*?),*?([^,]*?)(?=\t|\n)"
RE_COMMITTE_END = r"^\s{2}$"

RE_WITNESS_BEGIN = r"^\s+WITNESSES$"
RE_WITNESSES = r"^([^,]+?),(.+?)(?=\n)"
RE_WITNESS_END = r"^$"

RE_CONTENT_BLOCKS = r"(\n{2}\s+[0-9A-Z\s\.\(\)\n\-,]+\n{2})(.+?)(?=\s+[0-9A-Z\s\.\(\\)\-,]+\n{2})"
RE_SPEAKERS = r"(?<=\s{4})(Mr\.|Mrs\.|Ms\.|General|Secretary)\s([\w-]+)(\s\[\w+\])*\.(.*?)(?=(\n{2,}|\s{4,}\[|\s{4,}(Mr\.|Mrs\.|Ms\.|General|Secretary)\s[\w-]+\.))"


def main() -> None:
    """Main function"""

    args = parse_cli_args()
    output = preprocess_document(args.file)
    save_output(args.output, output)


def parse_cli_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments.
    """

    parser = argparse.ArgumentParser(description='DoD Hearing document parser')
    parser.add_argument('-i', '--input', dest='input', required=True, help='Path to input file')
    parser.add_argument('-o', '--output', dest='output', required=True, help='Path to output file')
    return parser.parse_args()


def preprocess_document(path: str) -> dict:
    """
    Preprocess the input file.
    
    Args:
        path (str): The path of the file to preprocess.

    Returns:
        dict: The preprocessed data.
    """

    output = {
        'committee': [],
        'witnesses': [], 
        'content': [],
    }

    with open(path, 'r') as file:
        while True:
            line = file.readline()

            if re.match(RE_COMMITTEE_BEGIN, line):
                buffer = StringIO()

                while not re.match(RE_COMMITTE_END, line):
                    line = file.readline()
                    buffer.write(line)

                buffer.seek(0)
                parser = re.compile(RE_COMMITTEE_MEMBERS, flags=(re.MULTILINE | re.DOTALL))

                for match in parser.finditer(buffer.read()):
                    output['committee'].append({
                        'name': match.group(1).strip(),
                        'district': match.group(2).strip(),
                        'title': match.group(3).strip(),
                    })

                break

        while True:
            line = file.readline()

            if re.match(RE_WITNESS_BEGIN, line):
                buffer = StringIO()
                file.readline() # skip empty line
                line = file.readline()

                while not re.match(RE_WITNESS_END, line):
                    buffer.write(line)
                    line = file.readline()

                buffer.seek(0)
                parser = re.compile(RE_WITNESSES, flags=(re.MULTILINE | re.DOTALL))

                for match in parser.finditer(buffer.read()):
                    output['witnesses'].append({
                        'name': match.group(1).strip(),
                        'title': match.group(2).strip(),
                    })

                break

        buffer = StringIO(file.read())
        content_blocks = re.compile(RE_CONTENT_BLOCKS, flags=(re.MULTILINE | re.DOTALL))
        speakers = re.compile(RE_SPEAKERS, flags=(re.MULTILINE | re.DOTALL))

        for content_block in content_blocks.finditer(buffer.read()):
            topic = re.sub('\s+', ' ', content_block.group(1).strip())
            body = content_block.group(2)

            for speaker in speakers.finditer(body):
                title = speaker.group(1).strip()
                name = speaker.group(2).strip()
                remarks = speaker.group(4).translate(str.maketrans('', '', '\r\n\t'))
                remarks = " ".join(remarks.split())
                word_count = len(remarks.split())

                output['content'].append({
                    'topic': topic,
                    'title': title,
                    'name': name,
                    'word_count': word_count,
                    'remarks': remarks,
                })

    return output


def save_output(path: str, output: dict) -> None:
    """
    Save the output to a file.
    
    Args:
        path (str): The path to the file to save to.
        output (dict): The output to save.
    """

    with open(path, 'w') as file:
        json.dump(output, file, indent=4)


if __name__ == "__main__":
    main()
