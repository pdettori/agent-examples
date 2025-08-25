# Slack MCP Server

This is a simple Slack MCP Server with two tools:

- `get_channels` to list all public and private channels the bot has access to
- `get_channel_history` to list messages from a specific channel by `channel_id`

You can configure the server with the following environment variables:

| Variable name            | Required? | Default                | Description |
| ------------------------ | --------- | ---------------------- | ----------------------------- |
| `SLACK_BOT_TOKEN`        | Yes       | `YOUR_SLACK_BOT_TOKEN` | Access token for the Slack server |
| `LOG_LEVEL`              | No        | `INFO`                 | Application log level |
| `MCP_TRANSPORT`          | No        | `streamable-http`      | Passed into mcp.run to determine mcp transport |
| `ISSUER`                 | No        | - | If populated, will publish that it is OAuth-secured by this issuer (but no actual verification). Must be URI format |
| `INTROSPECTION_ENDPOINT` | No        | - | If populated, will extract access tokens from requests and introspect them here |
| `AUDIENCE `              | No.       | - | If populated with `INTROSPECTION_ENDPOINT` will perform audience validation |

You can run this locally with `uv run slack_tool.py` so long as the `SLACK_BOT_TOKEN` is set. 

## Auth setting

If `ISSUER` is set, the server will extract and print the bearer token, and fail if there is no bearer token. There is no official token validation at this time - this is purely for testing. 
