"""
Humanness Evaluator — MCP Server

Exposes OASis humanness evaluation and Sapiens humanization as MCP tools.
Designed for deployment on Azure Container Apps with HTTP/SSE transport.

Tools:
  - evaluate_humanness   : Single VH sequence OASis evaluation
  - evaluate_batch       : Multiple sequences from JSON input
  - humanize_antibody    : Full Sapiens humanization (before/after)
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

# Add skill root to sys.path so bundled agent_api is importable
SKILL_ROOT = Path(__file__).parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

server = Server("humanness-evaluator")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="evaluate_humanness",
            description=(
                "Evaluate OASis humanness score for a single antibody VH sequence. "
                "Returns OASis Identity (%), percentile, germline content, and germline gene assignments. "
                "Use when the user wants to check immunogenicity risk of one antibody sequence."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vh_seq": {
                        "type": "string",
                        "description": "Heavy chain amino acid sequence (required)"
                    },
                    "vl_seq": {
                        "type": "string",
                        "description": "Light chain amino acid sequence (optional)"
                    },
                    "sequence_id": {
                        "type": "string",
                        "description": "Label for this sequence in the output",
                        "default": ""
                    },
                    "min_fraction_subjects": {
                        "type": "number",
                        "description": "OASis subject frequency threshold (default 0.1 = 10%)",
                        "default": 0.1
                    }
                },
                "required": ["vh_seq"]
            }
        ),
        Tool(
            name="evaluate_batch",
            description=(
                "Evaluate OASis humanness scores for multiple antibody sequences at once. "
                "Accepts a JSON list of sequences and returns metrics for each. "
                "Use for batch screening of designed antibody libraries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sequences": {
                        "type": "array",
                        "description": "List of sequence objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "vh_seq": {"type": "string"},
                                "vl_seq": {"type": "string"},
                                "sequence_id": {"type": "string"}
                            },
                            "required": ["vh_seq"]
                        }
                    },
                    "min_fraction_subjects": {
                        "type": "number",
                        "default": 0.1
                    }
                },
                "required": ["sequences"]
            }
        ),
        Tool(
            name="humanize_antibody",
            description=(
                "Run full Sapiens humanization on a VH sequence and compare OASis humanness before/after. "
                "Returns mutations applied, OASis identity improvement, germline changes, and a summary. "
                "Use when the user wants to humanize an antibody or see how humanization improved humanness."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vh_seq": {
                        "type": "string",
                        "description": "Heavy chain amino acid sequence to humanize"
                    },
                    "vl_seq": {
                        "type": "string",
                        "description": "Light chain sequence (optional)"
                    },
                    "scheme": {
                        "type": "string",
                        "description": "Numbering scheme: imgt / kabat / chothia",
                        "default": "imgt"
                    },
                    "sapiens_iterations": {
                        "type": "integer",
                        "description": "Number of Sapiens humanization iterations",
                        "default": 1
                    },
                    "humanize_cdrs": {
                        "type": "boolean",
                        "description": "Whether to humanize CDR regions (default: False — retain parental CDRs)",
                        "default": False
                    },
                    "min_fraction_subjects": {
                        "type": "number",
                        "default": 0.1
                    }
                },
                "required": ["vh_seq"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    loop = asyncio.get_event_loop()

    if name == "evaluate_humanness":
        result = await loop.run_in_executor(None, _evaluate_humanness, arguments)

    elif name == "evaluate_batch":
        result = await loop.run_in_executor(None, _evaluate_batch, arguments)

    elif name == "humanize_antibody":
        result = await loop.run_in_executor(None, _humanize_antibody, arguments)

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Tool implementations (run in thread pool — agent_api calls are synchronous)
# ---------------------------------------------------------------------------

def _evaluate_humanness(args: dict) -> dict:
    try:
        from agent_api import evaluate_humanness
        with tempfile.TemporaryDirectory() as tmp:
            raw = evaluate_humanness(
                vh_seq=args["vh_seq"],
                vl_seq=args.get("vl_seq"),
                min_fraction_subjects=args.get("min_fraction_subjects", 0.1),
                output_dir=tmp,
            )
        return {
            "sequence_id": args.get("sequence_id", ""),
            "oasis_identity": raw.get("oasis_identity"),
            "oasis_identity_vh": raw.get("oasis_identity_vh"),
            "oasis_identity_vl": raw.get("oasis_identity_vl"),
            "oasis_percentile": raw.get("oasis_percentile"),
            "germline_content": raw.get("germline_content"),
            "germlines": raw.get("germlines", {}),
            "summary": raw.get("summary", ""),
            "interpretation": _interpret(raw.get("oasis_identity")),
        }
    except Exception as e:
        return {"error": str(e)}


def _evaluate_batch(args: dict) -> dict:
    sequences = args.get("sequences", [])
    threshold = args.get("min_fraction_subjects", 0.1)
    results = []

    for seq in sequences:
        result = _evaluate_humanness({**seq, "min_fraction_subjects": threshold})
        results.append(result)

    successful = [r for r in results if "error" not in r]
    scores = [r["oasis_identity"] for r in successful if r.get("oasis_identity") is not None]

    summary = {
        "total": len(results),
        "successful": len(successful),
        "failed": len(results) - len(successful),
    }
    if scores:
        summary.update({
            "mean_oasis_identity": round(sum(scores) / len(scores), 2),
            "min_oasis_identity": round(min(scores), 2),
            "max_oasis_identity": round(max(scores), 2),
            "pass_threshold_70": sum(1 for s in scores if s >= 70),
        })

    return {"summary": summary, "results": results}


def _humanize_antibody(args: dict) -> dict:
    try:
        from agent_api import humanize_antibody_sequence
        with tempfile.TemporaryDirectory() as tmp:
            raw = humanize_antibody_sequence(
                vh_seq=args["vh_seq"],
                vl_seq=args.get("vl_seq"),
                scheme=args.get("scheme", "imgt"),
                cdr_definition=args.get("scheme", "imgt"),
                sapiens_iterations=args.get("sapiens_iterations", 1),
                humanize_cdrs=args.get("humanize_cdrs", False),
                min_fraction_subjects=args.get("min_fraction_subjects", 0.1),
                output_dir=tmp,
            )
        return {
            "vh_mutations": raw.get("vh_mutations", []),
            "vl_mutations": raw.get("vl_mutations", []),
            "before": raw.get("before", {}),
            "after": raw.get("after", {}),
            "germlines": raw.get("germlines", {}),
            "summary": raw.get("summary", ""),
        }
    except Exception as e:
        return {"error": str(e)}


def _interpret(score) -> str:
    if score is None:
        return "N/A"
    if score > 75:
        return "Excellent (>75%) — ready for clinic"
    if score > 70:
        return "Good (70-75%) — acceptable"
    if score > 60:
        return "Fair (60-70%) — consider optimization"
    if score > 50:
        return "Poor (50-60%) — recommend redesign"
    return "Very Poor (<50%) — needs major changes"


# ---------------------------------------------------------------------------
# Starlette app with SSE transport (for remote MCP over HTTP)
# ---------------------------------------------------------------------------

sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )


async def health(request: Request):
    return JSONResponse({"status": "ok", "server": "humanness-evaluator"})


app = Starlette(
    routes=[
        Route("/health", health),
        Route("/sse", handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
