import os
import json

# PDF generation is disabled. Evidence is stored as JSON metadata only.


def generate_citation_pdf(ticket_id: str, citation_data: dict, output_dir: str = "evidence_pdfs") -> str:
    """PDF generation is disabled. Returns empty string."""
    return ""


def generate_citation_json(ticket_id: str, citation_data: dict, output_dir: str = "evidence_pdfs") -> str:
    """Saves citation metadata as JSON evidence file."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{ticket_id}.json")
    with open(json_path, "w") as f:
        json.dump(citation_data, f, indent=4)
    return json_path
