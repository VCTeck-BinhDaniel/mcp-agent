from __future__ import annotations

import json
from typing import Any

from fastmcp import Context, FastMCP
from RSPileScripting.RSPileModeler import RSPileModeler

mcp = FastMCP[Any]("rspile-nano-server")

DEFAULT_PORT = 60044
_model: dict[str, Any] = {
    "modeler": None,
    "model": None,
    "model_path": None,
    "port": DEFAULT_PORT,
}


def _require_model() -> Any:
    model = _model.get("model")
    if model is None:
        raise RuntimeError("No model is open. Call open_model first.")
    return model


@mcp.tool(
    name="startrspile",
    description="Open the RSPile application.",
)
async def start_rspile(port: int = DEFAULT_PORT) -> str:
    """Start RSPile on the given port."""
    RSPileModeler.startApplication(port)
    modeler = RSPileModeler(port)
    _model["port"] = port
    _model["modeler"] = modeler
    return f"RSPile started on port {port}."


@mcp.tool(
    name="closerspile",
    description="Close the RSPile application.",
)
async def close_rspile(port: int = DEFAULT_PORT) -> str:
    """Close RSPile on the given port."""
    target_port = _model.get("port", port)
    RSPileModeler(target_port).closeApplication()
    _model["modeler"] = None
    _model["model"] = None
    _model["model_path"] = None
    return "RSPile closed."


@mcp.tool(
    name="openmodel",
    description="Open an RSPile model file.",
)
async def open_model(ctx: Context, model_path: str, port: int = DEFAULT_PORT) -> str:
    """Open a .rspile2 model and keep it in memory for later tools."""
    modeler = _model.get("modeler")
    await ctx.info(f"open_model: modeler: {type(modeler)}")
    if modeler is None:
        RSPileModeler.startApplication(port)
        modeler = RSPileModeler(port)
    else:
        # Reuse existing app/modeler session instead of launching again.
        port = int(_model.get("port", port))
    model = modeler.openFile(model_path)
    _model["port"] = port
    _model["modeler"] = modeler
    _model["model"] = model
    _model["model_path"] = model_path
    return json.dumps(
        {
            "ok": True,
            "port": port,
            "model_path": model_path,
            "message": "Model opened.",
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool(
    name="runcompute",
    description="Run compute for the currently opened model.",
)
async def run_compute() -> str:
    """Save and compute the currently opened model."""
    model = _require_model()
    model.save()
    model.compute()
    return json.dumps(
        {
            "ok": True,
            "model_path": _model.get("model_path"),
            "message": "Compute finished.",
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool(name="readresults", description="Return pile result tables.")
async def read_results(ctx: Context) -> str:
    model = _require_model()
    tables = model.getPileResultsTables()
    await ctx.info(f"read_results: tables: {tables}")
    payload = {
        pile_id: table.to_dict(orient="records") for pile_id, table in tables.items()
    }

    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


@mcp.tool(name="savemodel", description="Save the currently opened model.")
async def save_model(ctx: Context, file_name: str) -> str:
    model = _require_model()
    model.save(file_name)
    await ctx.info(f"save_model: file_name: {file_name}")
    return json.dumps(
        {
            "ok": True,
            "model_path": file_name,
            "message": "New version of model saved.",
        },
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
