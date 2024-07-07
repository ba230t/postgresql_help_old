"""
PostgreSQL Help Flask application.

Usage:
    1. open localhost:5000
    2. select versions
    3. press "Compare"
"""

import os
import difflib
from flask import Flask, render_template, request

app = Flask(__name__)

def get_postgresql_versions():
    """
    Get available PostgreSQL versions from the help_files directory.

        Usage:
            >>> get_postgresql_versions()
            ['postgres_9.6', 'postgres_10', ...]

    :return: List of available PostgreSQL versions, e.g. ["postgres_9.6", "postgres_10", ...].
    """
    help_files_dir = "help_files"
    directories = [d.name for d in os.scandir(help_files_dir) if d.is_dir() and d.name.startswith("postgres_")]
    return sorted(directories, key=lambda x: float(x.split('_')[1]))


@app.route("/")
def index():
    """
    Render the index page with a list of PostgreSQL versions.

    :return: Rendered HTML template for the index page.
    """
    versions = get_postgresql_versions()
    return render_template("index.html", versions=versions)


@app.route("/compare", methods=["POST"])
def compare():
    """
    Handle a request for comparing selected versions of PostgreSQL help files.

    :return: Rendered HTML template for the comparison results.
    """
    selected_versions = request.form.getlist("versions")
    if len(selected_versions) < 2:
        return "Please select at least two versions for comparison.", 400

    diff_results = compare_versions(selected_versions)
    return render_template(
        "compare.html", versions=selected_versions, diff_results=diff_results
    )


def compare_versions(versions):
    """
    Compare the help files of the selected PostgreSQL versions.

    Usage:
        >>> compare_versions(["postgres_10", "postgres_11"])
        {
            'ALTER DEFAULT PRIVILEGES':{
                'postgres_10': '<pre>...</pre>',
                'postgres_11': '<pre>...</pre>'
            },
            'ALTER DOMAIN':{ ... },
            ...
        }

    :param versions: List of selected PostgreSQL versions.
    :return: Dictionary containing the differences for each command.
    """
    help_files = {version: get_help_files(version) for version in versions}

    all_commands = set()
    for files in help_files.values():
        all_commands.update(files.keys())

    diffs = {}

    for cmd in sorted(all_commands):
        # ex. "{'postgres_10': '<HELP_TEXT>', 'postgres_11': '<HELP_TEXT>'}"
        cmd_versions = {
            version: help_files[version].get(cmd, "") for version in versions
        }
        if any(
            cmd_versions[version] != cmd_versions[versions[0]]
            for version in versions[1:]
        ):
            diffs[cmd] = highlight_diff(cmd_versions)

    return diffs


def highlight_diff(cmd_versions):
    """
    Highlight the differences between the help texts.

    Usage:
        >>> highlight_diff({
            'postgres_10': '<HELP_TEXT>',
            'postgres_11': '<HELP_TEXT>'})
        {'postgres_10': '<pre><span class="unchanged"><HELP_TEXT></span></pre>',
         'postgres_11': '<pre><span class="unchanged"><HELP_TEXT></span></pre>'}

        >>> highlight_diff({
            'postgres_10': '<HELP\nHELP10>',
            'postgres_11': '<HELP\nHELP11>'})
        {'postgres_10': '<pre><span class="unchanged"><HELP</span>\n<span class="deleted" style="background-color: #ffeef0;">HELP10></span></pre>',
         'postgres_11': '<pre><span class="unchanged"><HELP</span>\n<span class="added" style="background-color: #e6ffed;">HELP11></span></pre>'}

    :param cmd_versions: Dictionary of help texts for a command for each version.
    :return: Dictionary of highlighted differences for each version.
    """
    highlighted = {}
    versions = list(cmd_versions.keys())

    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            v1, v2 = versions[i], versions[j]
            lines1 = cmd_versions[v1].splitlines()
            lines2 = cmd_versions[v2].splitlines()

            d = difflib.Differ()
            diff = list(d.compare(lines1, lines2))

            highlighted_1 = []
            highlighted_2 = []

            for line in diff:
                if line.startswith("  "):
                    highlighted_1.append(f'<span class="unchanged">{line[2:]}</span>')
                    highlighted_2.append(f'<span class="unchanged">{line[2:]}</span>')
                elif line.startswith("- "):
                    highlighted_1.append(
                        f'<span class="deleted" style="background-color: #ffeef0;">{line[2:]}</span>'
                    )
                elif line.startswith("+ "):
                    highlighted_2.append(
                        f'<span class="added" style="background-color: #e6ffed;">{line[2:]}</span>'
                    )

            highlighted[v1] = "<pre>" + "\n".join(highlighted_1) + "</pre>"
            highlighted[v2] = "<pre>" + "\n".join(highlighted_2) + "</pre>"

    return highlighted


def get_help_files(version):
    """
    Read all help files for the specific PostgreSQL version.

    Usage:
        >>> get_help_files("postgres_10")
        {'ABORT': '<FILE_CONTENT>',
         'ALTER AGGREGATE': '<FILE_CONTENT>',
         ...
        }

    :param version: PostgreSQL version.
    :return: Dictionary containing the help texts for each command.
    """
    help_dir = f"help_files/{version}"
    help_files = {}
    for filename in os.listdir(help_dir):
        with open(os.path.join(help_dir, filename), "r", encoding="utf-8") as file:
            help_files[filename.replace(".txt", "")] = file.read()
    return help_files


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
