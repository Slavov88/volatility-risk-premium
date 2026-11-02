"""Render the standalone manuscript with Pandoc 3.1.3 and Typst 0.15.0.

Install the paper requirements, then run from any directory. Outputs are placed
beside the source. Provider observations are not required for typesetting.
"""

from pathlib import Path
import re
import subprocess
import tempfile
import typst

HERE = Path(__file__).resolve().parent


def unbox(source):
    while "\\boxed{" in source:
        start = source.index("\\boxed{")
        cursor = start + len("\\boxed{")
        depth = 1
        while depth:
            if source[cursor] == "{":
                depth += 1
            elif source[cursor] == "}":
                depth -= 1
            cursor += 1
        source = (
            source[:start]
            + source[start + len("\\boxed{") : cursor - 1]
            + source[cursor:]
        )
    return source


def render(stem="manuscript"):
    source = unbox((HERE / (stem + ".md")).read_text())
    # Removing a decorative box must not introduce a blank paragraph into math.
    source = re.sub(
        r"\\\[(.*?)\\\]",
        lambda match: "\\["
        + "\n".join(line for line in match[1].splitlines() if line.strip())
        + "\\]",
        source,
        flags=re.S,
    )
    source = re.sub(
        r"\\begin\{center\}\\includegraphics\[width=0\.88\\linewidth\]\{figures/([^}]+)\.pdf\}\\end\{center\}",
        lambda match: "![](figures/" + match[1] + ".svg){width=88%}",
        source,
    )
    with tempfile.TemporaryDirectory(prefix="render-", dir=HERE) as directory:
        markdown = Path(directory) / "source.md"
        compiled = Path(directory) / "source.typ"
        markdown.write_text(source)
        subprocess.run(
            [
                "pandoc",
                str(markdown),
                "--from=markdown+tex_math_single_backslash",
                "--to=typst",
                "--standalone",
                "--template=" + str(HERE / "layout.typ"),
                "-o",
                str(compiled),
            ],
            check=True,
        )
        # Figure paths are relative to the typeset source rather than temporary input.
        document = HERE / (stem + ".typ")
        document.write_text(compiled.read_text())
        try:
            typst.compile(
                str(document),
                output=str(HERE / (stem + ".pdf")),
                root=str(HERE),
                font_paths=["/usr/share/texmf/fonts/opentype/public/lm"],
            )
        except typst.TypstError as error:
            raise RuntimeError(error.diagnostic) from error
        finally:
            document.unlink(missing_ok=True)


if __name__ == "__main__":
    render()
