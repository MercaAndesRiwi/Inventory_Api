"""Entry point to run the application directly."""

from __future__ import annotations

import uvicorn

from inventory.infrastructure.config import API_HOST, API_PORT


def main() -> None:
    """Starts the inventory API server."""
    print(f"Starting inventory API on {API_HOST}:{API_PORT}")
    print(f"Documentation available at http://{API_HOST}:{API_PORT}/docs")

    uvicorn.run(
        "inventory.presentation.fastapi.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
