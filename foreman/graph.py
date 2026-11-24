"""
Graph blueprint.

Renders the whole repository as an interactive provenance DAG: one node per job,
one edge per r3 *job* dependency (git dependencies are not jobs, so they are omitted).
Nodes are colored by job type (inferred from tags) and link to the job's detail page.
"""
import json

import r3
from flask import Blueprint, render_template, url_for

from foreman.r3_extension import Repository

graph = Blueprint("graph", __name__, url_prefix="/graph")


def _group(tags: list[str]) -> str:
    """Coarse job type from tags, for node coloring."""
    t = set(tags or [])
    if "entry-node" in t or "dataset" in t:
        return "entry"
    if "report" in t or "analysis" in t:
        return "report"
    if "compute" in t or "sweep" in t or "train" in t:
        return "compute"
    return "other"


@graph.route("/")
def view():
    repository = Repository.from_environment()
    jobs = list(repository.jobs())

    nodes = []
    for job in jobs:
        jid = str(job.id)
        label = job.virtual_path or job.name or jid[:8]
        tags = job.tags
        nodes.append(
            {
                "id": jid,
                "label": label,
                "title": "\n".join(
                    [
                        job.virtual_path or "",
                        f"id: {jid}",
                        f"status: {job.status}",
                        f"tags: {', '.join(tags)}" if tags else "",
                    ]
                ).strip(),
                "group": _group(tags),
                "url": url_for("job.view", id=jid),
            }
        )

    edges = []
    for job in jobs:
        jid = str(job.id)
        for dependency in job.r3_job.dependencies:
            if not isinstance(dependency, r3.JobDependency):
                continue  # git dependency -> not a node in this graph
            edges.append({"from": str(dependency.job), "to": jid})

    return render_template(
        "graph/view.html.jinja",
        nodes=json.dumps(nodes),
        edges=json.dumps(edges),
        job_count=len(nodes),
        edge_count=len(edges),
    )
