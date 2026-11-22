from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(r"C:\ck3_workshop_upload")
CONTENT = Path(
    r"C:\Users\kmkjk\OneDrive\Documents\Paradox Interactive\Crusader Kings III\mod\imperial_fragmentation"
)
CHANGENOTE = "Version 1.2 for Crusader Kings III 1.21. Fixed conquest modifiers that stopped working after the 1.21 county rework. New: conquest costs prosperity and disrupts trade markets, low-control conquests catch county corruption, dispossessed lords can fight to take their land back, ruler stewardship and government type change strain, Harsh Pacification and Consolidate the Realm decisions, Unrest in the Provinces event, and a game rule to spare AI realms. Integrate a Conquered Province now needs 25 control."


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def main() -> None:
    published = ROOT / "publishedfileid.txt"
    file_id = published.read_text().split()[0] if published.exists() else "0"
    description = (ROOT / "description.txt").read_text(encoding="utf-8").strip()
    fields = {
        "appid": "1158310",
        "publishedfileid": file_id,
        "contentfolder": str(CONTENT),
        "previewfile": str(ROOT / "preview.jpg"),
        "visibility": "0",
        "title": "Imperial Fragmentation",
        "description": description,
        "changenote": CHANGENOTE,
    }
    body = "\n".join(f'\t"{k}"\t\t"{esc(v)}"' for k, v in fields.items())
    UPLOAD_DIR.mkdir(exist_ok=True)
    out = UPLOAD_DIR / "imperial_fragmentation.vdf"
    out.write_text('"workshopitem"\n{\n' + body + "\n}\n", encoding="utf-8")
    print(out, len(description), "chars")


if __name__ == "__main__":
    main()
