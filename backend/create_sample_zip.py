from pathlib import Path
import zipfile


def write_file(base: Path, relative_path: str, content: str) -> None:
    target = base / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build_sample_tree(temp_dir: Path) -> None:
    write_file(temp_dir, "README.md", """# Sample Project\n\nThis is a small sample project for testing ingestion.\n""")

    write_file(temp_dir, "docs/guide.md", """## Guide\n\n- Step 1: Install\n- Step 2: Run\n\nSome additional documentation details.\n""")

    write_file(
        temp_dir,
        "src/app.py",
        """from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/hello')\ndef hello():\n    return {'message': 'hello world'}\n""",
    )

    write_file(
        temp_dir,
        "src/utils/math.js",
        """export function add(a, b) {\n  return a + b;\n}\n\nexport function mul(a, b) {\n  return a * b;\n}\n""",
    )

    write_file(
        temp_dir,
        "config/settings.yaml",
        """app:\n  name: sample\n  debug: true\n""",
    )

    write_file(temp_dir, "data/example.txt", "This is an example text file used for testing.\n")


def create_zip(output_zip: Path) -> None:
    temp_root = output_zip.parent / "_sample_zip_tmp"
    if temp_root.exists():
        # Clean previous run
        for p in sorted(temp_root.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            else:
                try:
                    p.rmdir()
                except OSError:
                    pass
        try:
            temp_root.rmdir()
        except OSError:
            pass

    temp_root.mkdir(parents=True, exist_ok=True)
    build_sample_tree(temp_root)

    # Write ZIP
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in temp_root.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(temp_root))

    # Best-effort cleanup of temp tree
    for p in sorted(temp_root.rglob("*"), reverse=True):
        if p.is_file():
            try:
                p.unlink()
            except OSError:
                pass
        else:
            try:
                p.rmdir()
            except OSError:
                pass
    try:
        temp_root.rmdir()
    except OSError:
        pass


if __name__ == "__main__":
    backend_dir = Path(__file__).resolve().parent
    output_zip = backend_dir / "sample_docs.zip"
    create_zip(output_zip)
    print(f"Created sample ZIP at: {output_zip}")


