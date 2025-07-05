import asyncio
import os

from neo4j import AsyncGraphDatabase
from mcp_neo4j_cypher.server import create_mcp_server


async def main() -> None:
    """Run the Neo4j MCP server using SSE transport."""
    driver = AsyncGraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(
            os.getenv("NEO4J_USERNAME", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password"),
        ),
    )

    mcp = create_mcp_server(
        driver,
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        namespace=os.getenv("NEO4J_NAMESPACE", ""),
        host="0.0.0.0",
        port=int(os.getenv("PORT", os.getenv("NEO4J_MCP_SERVER_PORT", 8000))),
    )

    await mcp.run_sse_async()


if __name__ == "__main__":
    asyncio.run(main())
