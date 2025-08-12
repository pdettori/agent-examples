# Slack Researcher Agent

## Introduction

The Slack Researcher Agent is designed to perform research tasks across Slack channels, leveraging large language models (LLMs) to generate plans, execute steps, and summarize findings. This agent integrates with Slack as a tool via MCP and utilizes AI models for data extraction, summarization, and more. The architecture enables iterative task decomposition, allowing the agent to handle complex tasks by breaking them down into smaller steps.

## Architecture

![alt text](docs/image.png)

### Configuration Variables

| Variable Name | Description | Default Value | 
|---------------|-------------|---------------| 
| OPENAI_API_URL | The URL for OpenAI compatible API | `http://localhost:11434/v1` | 
| OPENAI_API_KEY | The key for OpenAI compatible API | `ollama` |
| TASK_MODEL_ID | The ID of the LLM | `granite3.3:8b` | 
| EXTRA_HEADERS | Extra headers for the OpenAI API, e.g. {"MY_HEADER": "my_value"} | `{}` | 
| MODEL_TEMPERATURE | The temperature for the model | `0` | 
| MAX_PLAN_STEPS | The maximum number of plan steps | `6` | 
| MCP_ENDPOINT | Endpoint where the Slack MCP server can be found | "" | 
| SERVICE_PORT | Port on which the service will run | `8000` |
