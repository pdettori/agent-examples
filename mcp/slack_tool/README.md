# Slack MCP Server

This is a simple Slack MCP Server with two tools:

- `get_channels` to list all public and private channels the bot has access to
- `get_channel_history` to list messages from a specific channel by `channel_id`

You can configure the server with the following environment variables:

| Variable name     | Required? | Default                | Description |
| ----------------- | --------- | ---------------------- | ----------------------------- |
| `SLACK_BOT_TOKEN` | Yes       | `YOUR_SLACK_BOT_TOKEN` | Access token for the Slack server |
| `MCP_TRANSPORT`   | No        | `streamable-http`      | Passed into mcp.run to determine mcp transport |
| `ISSUER`          | No        | `your-oauth-provider`  | If populated, will attempt to extract bearer token, fail otherwise |

You can run this locally with `uv run slack_tool.py` so long as the `SLACK_BOT_TOKEN` is set. 

