# hermes-memory: MCP-native persistent memory for LLM agents
# https://github.com/Mibayy/hermes-memory (MIT)
# stdio MCP server, exposed as streamablehttp via mcp-proxy so remote
# agents (pi/GLM, DeepSeek, Qwen) can share one mutable memory store.
#
# Pinned combination verified 2026-09-12: both packages declare only
# lower bounds on the `mcp` SDK (>=1.0.0 / >=1.17.0) and BREAK against
# mcp 2.x (Server.list_tools and lowlevel.request_ctx were removed).
# Pin mcp to 1.x explicitly.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      hermes-memory==0.3.0 \
      mcp-proxy==0.12.0 \
      "mcp>=1.17.0,<2"

RUN useradd --create-home --uid 1000 hermes
USER hermes

ENV HERMES_MEMORY_DB=/data/memory.db
EXPOSE 8080

# mcp-proxy wraps the stdio MCP server as a network transport.
# --transport streamablehttp verified against mcp-proxy 0.12.0.
ENTRYPOINT ["mcp-proxy", "--host", "0.0.0.0", "--port", "8080", "--transport", "streamablehttp", "--"]
CMD ["hermes-memory"]
