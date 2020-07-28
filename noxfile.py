import shutil
import sys

import nox

sys.path.insert(0, "")
from src.helpers import BUILD_PATH, PUBLIC_PATH, RENDER_INFO_FILE, load_themes


def _prepare_output_directory(destination):
    # Clean up existing stuff
    if destination.exists():
        shutil.rmtree(destination)

    # Make the barebones skeleton
    destination.mkdir()
    (destination / "preview-images").mkdir()
    (destination / "sample-sites").mkdir()


def _generate_docs(session, theme):
    RENDER_INFO_FILE.write_text(repr(vars(theme)))
    try:
        session.run("python", "tools/render-theme.py", theme.name, silent=True)
    finally:
        RENDER_INFO_FILE.unlink()

    shutil.move(
        str(BUILD_PATH / theme.name), str(PUBLIC_PATH / "sample-sites" / theme.name),
    )


def _generate_preview(session, theme):
    # Generate the preview
    session.run(
        "python",
        "tools/generate-preview.py",
        str(BUILD_PATH / theme.name / "index.html"),
        theme.name,
        silent=True,
    )


def with_every_theme(session, function, message):
    """Nice little helper, to make looping through all the themes easier.
    """
    themes = load_themes()
    failed = []
    for theme in themes:
        try:
            function(session, theme)
        except Exception:
            failed.append(theme)
            continue

    if failed:
        parts = [f"Failed to {message.lower()} for:"]
        for theme in failed:
            parts.append(f"- {theme.name}")
        session.error("\n".join(parts))


@nox.session(python=False)
def publish(session):
    session.notify("render-sample-sites")
    session.notify("generate-previews")
    session.notify("render-index")


@nox.session(name="render-sample-sites")
def render_sample_sites(session):
    _prepare_output_directory(PUBLIC_PATH)
    _prepare_output_directory(BUILD_PATH)

    session.install("virtualenv")
    with_every_theme(session, _generate_docs, "Render")


@nox.session(name="generate-previews")
def generate_previews(session):
    assert BUILD_PATH.exists(), "Did you run 'render-sample-sites' yet?"

    session.install("selenium", "pillow")
    with_every_theme(session, _generate_preview, "Generate preview")

    shutil.move(BUILD_PATH / "preview-images", PUBLIC_PATH / "preview-images")


@nox.session(name="render-index")
def render_index(session):
    session.install("jinja2")
    session.run("python", "tools/render-index.py")
