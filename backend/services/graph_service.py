"""
services/graph_service.py

WHY compute the graph on the backend?
  The frontend only needs {nodes, links} — a clean, simple structure.
  All the messy tag-splitting, deduplication, and weight calculation
  stays server-side and out of React.

Graph model:
  Nodes  — one per note + one per unique tag
  Links  — note→tag (always) + note→note when they share tags
  Weight — number of shared tags between two notes (thicker edge = stronger link)
"""
from models import Note


def build_graph(user_id: int) -> dict:
    notes = Note.query.filter_by(user_id=user_id).all()

    if not notes:
        return {"nodes": [], "links": []}

    nodes = []
    links = []
    tag_nodes = {}   # tag_name → node id (to avoid duplicates)

    # ── 1. Note nodes ─────────────────────────────────────────────────
    for note in notes:
        nodes.append({
            "id":       f"note_{note.id}",
            "type":     "note",
            "label":    note.title[:40] + ("…" if len(note.title) > 40 else ""),
            "color":    note.color or "#1e1e2e",
            "pinned":   note.is_pinned,
            "has_summary": bool(note.summary),
            "tags":     [t.strip() for t in (note.tags or "").split(",") if t.strip()],
            "note_id":  note.id,
        })

    # ── 2. Tag nodes + note→tag links ────────────────────────────────
    for note in notes:
        tags = [t.strip() for t in (note.tags or "").split(",") if t.strip()]
        for tag in tags:
            tag_id = f"tag_{tag}"
            if tag_id not in tag_nodes:
                tag_nodes[tag_id] = tag
                nodes.append({
                    "id":    tag_id,
                    "type":  "tag",
                    "label": f"#{tag}",
                    "color": "#7c5cfc",
                })
            links.append({
                "source": f"note_{note.id}",
                "target": tag_id,
                "weight": 1,
                "type":   "note_tag",
            })

    # ── 3. Note→Note links (shared tags) ─────────────────────────────
    note_tags = {}
    for note in notes:
        note_tags[note.id] = {
            t.strip() for t in (note.tags or "").split(",") if t.strip()
        }

    seen_pairs = set()
    note_ids = [n.id for n in notes]
    for i, id_a in enumerate(note_ids):
        for id_b in note_ids[i + 1:]:
            shared = note_tags[id_a] & note_tags[id_b]
            if shared:
                pair = (min(id_a, id_b), max(id_a, id_b))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    links.append({
                        "source": f"note_{id_a}",
                        "target": f"note_{id_b}",
                        "weight": len(shared),
                        "type":   "note_note",
                        "shared_tags": list(shared),
                    })

    return {
        "nodes": nodes,
        "links": links,
        "stats": {
            "note_count": len(notes),
            "tag_count":  len(tag_nodes),
            "link_count": len(links),
        },
    }
