import asyncio
import os

from neo4j import AsyncGraphDatabase
from mcp_neo4j_cypher.server import create_mcp_server


async def main() -> None:
    """Run the Neo4j MCP server using SSE transport."""
    db_url = os.getenv("NEO4J_URL") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    driver = AsyncGraphDatabase.driver(
        db_url,
        auth=(
            os.getenv("NEO4J_USERNAME", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password"),
        ),
    )

    mcp = create_mcp_server(
        driver,
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        namespace=os.getenv("NEO4J_NAMESPACE", ""),
        host=os.getenv("NEO4J_MCP_SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("NEO4J_MCP_SERVER_PORT", 8000))),
    )

    try:
        await mcp.run_sse_async()
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(main())
