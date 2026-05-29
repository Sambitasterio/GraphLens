"""Generate a dummy multi-page text PDF for ingestion testing.

Writes a real PDF (proper objects + xref) with selectable text, so
pdfplumber/pdfminer can extract it — no external libraries required.

Usage:
    python -m scripts.make_sample_pdf            # -> samples/sample.pdf
    python -m scripts.make_sample_pdf out.pdf
"""
import sys
from pathlib import Path

# A few paragraphs per page so chunking has something to chew on. The
# fictional content also gives GraphRAG (Phase 3) entities/relationships.
PAGES = [
    [
        "GraphLens Quarterly Report - Page 1: Overview",
        "",
        "Acme Robotics announced a strategic partnership with Globex Corporation",
        "in March 2026. The deal was led by Dr. Elena Voss, Acme's Chief",
        "Technology Officer, who previously worked at Initech for eight years.",
        "",
        "The partnership focuses on autonomous warehouse systems. Globex will",
        "supply the navigation software, while Acme provides the robotic hardware.",
        "Analysts at Hooli Capital estimate the joint market at 4.2 billion dollars.",
        "",
        "Sarah Chen, the project manager at Globex, reports directly to the CEO,",
        "Michael Torres. Sarah has coordinated three prior integrations and is",
        "considered the key liaison between the two engineering organizations.",
    ],
    [
        "GraphLens Quarterly Report - Page 2: Technology",
        "",
        "The autonomous navigation stack relies on a fusion of LIDAR and vision",
        "sensors. Dr. Elena Voss emphasized that the system reduces collision",
        "rates by 37 percent compared to the previous generation.",
        "",
        "Globex's software team, managed by Sarah Chen, built the path-planning",
        "module on top of an open-source graph library. The module computes",
        "optimal routes across a warehouse floor in under 50 milliseconds.",
        "",
        "Initech, Dr. Voss's former employer, remains a competitor in this space",
        "and recently filed two patents related to robotic gripper design.",
    ],
    [
        "GraphLens Quarterly Report - Page 3: Outlook",
        "",
        "Michael Torres, CEO of Globex, projects that the Acme partnership will",
        "generate 600 million dollars in revenue within the first two years.",
        "",
        "Hooli Capital increased its position in both companies following the",
        "announcement. The fund's lead analyst praised the complementary nature",
        "of Acme's hardware expertise and Globex's software capabilities.",
        "",
        "Risks include supply-chain constraints and the ongoing patent dispute",
        "with Initech. Dr. Elena Voss stated that mitigation plans are in place",
        "and that production targets for 2026 remain unchanged.",
    ],
]


def _escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _content_stream(lines: list[str]) -> bytes:
    parts = ["BT", "/F1 12 Tf", "72 760 Td", "16 TL"]
    for i, line in enumerate(lines):
        if i > 0:
            parts.append("T*")
        parts.append(f"({_escape(line)}) Tj")
    parts.append("ET")
    return ("\n".join(parts) + "\n").encode("latin-1")


def build_pdf(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []  # body of each object, index 0 -> object 1

    n_pages = len(pages)
    font_obj = 3
    # page object numbers start at 4, content objects interleaved after pages
    page_obj_nums = [4 + i for i in range(n_pages)]
    content_obj_nums = [4 + n_pages + i for i in range(n_pages)]

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)

    # 1: catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: pages tree
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())
    # 3: font
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    # page objects
    for i in range(n_pages):
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
            f"/Contents {content_obj_nums[i]} 0 R >>"
        )
        objects.append(page.encode())
    # content streams
    for i in range(n_pages):
        stream = _content_stream(pages[i])
        obj = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
        objects.append(obj)

    # assemble with byte-offset tracking for the xref table
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for idx, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{idx} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(out)
    count = len(objects) + 1
    out += f"xref\n0 {count}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("samples/sample.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(build_pdf(PAGES))
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes, {len(PAGES)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
