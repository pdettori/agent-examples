# Slack Researcher Agent

## Introduction

The Slack Researcher Agent is designed to perform research tasks across Slack channels, leveraging large language models (LLMs) to generate plans, execute steps, and summarize findings. This agent integrates with Slack as a tool via MCP and utilizes AI models for data extraction, summarization, and more. The architecture enables iterative task decomposition, allowing the agent to handle complex tasks by breaking them down into smaller steps.

## Architecture

![alt text](docs/architecture.png)

### Configuration Variables

| Variable Name | Description | Required? | Default Value | 
|---------------|-------------|-----------|---------------| 
| OPENAI_API_URL | The URL for OpenAI compatible API | Yes | `http://localhost:11434/v1` | 
| OPENAI_API_KEY | The API key for OpenAI compatible API | No |  `my_api_key` |
| TASK_MODEL_ID | The ID of the LLM | Yes | `granite3.3:8b` | 
| EXTRA_HEADERS | Extra headers for the OpenAI API, e.g. {"MY_HEADER": "my_value"} | No | `{}` | 
| MODEL_TEMPERATURE | The temperature for the model | Yes | `0` | 
| MAX_PLAN_STEPS | The maximum number of plan steps | Yes | `6` | 
| MCP_ENDPOINT | Endpoint where the Slack MCP server can be found | No |  "" | 
| SERVICE_PORT | Port on which the service will run | No | `8000` |
