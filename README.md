# Neo4j MCP Railway SSE Server

This repository provides a minimal setup for hosting the
[`mcp-neo4j-cypher`](https://pypi.org/project/mcp-neo4j-cypher/) server on
[Railway](https://railway.app) using Server Sent Events (SSE).

## Usage

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the Neo4j connection information as environment variables:
   - `NEO4J_URI` (default: `bolt://localhost:7687`)
   - `NEO4J_USERNAME` (default: `neo4j`)
   - `NEO4J_PASSWORD` (default: `password`)
   - `NEO4J_DATABASE` (default: `neo4j`)
   - `NEO4J_NAMESPACE` (optional prefix for tool names)
   - `PORT` or `NEO4J_MCP_SERVER_PORT` (default: `8000`)
3. Start the server:
   ```bash
   python railway_sse_server.py
   ```

The service listens on `0.0.0.0:$PORT` and exposes an SSE endpoint at `/sse`
compatible with any MCP client.

## License

This project is released under the MIT License.
