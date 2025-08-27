from slack_researcher.config import Settings
from slack_researcher.types import Plan, Reflection


class LLMConfig:
    def __init__(self, config: Settings):
        # Used for most agents
        self.openai_llm_config = {
            "config_list": [
            {
                "model": config.TASK_MODEL_ID,
                "base_url": config.LLM_API_BASE,
                "api_type": "openai",
                "api_key": config.LLM_API_KEY,
                **(
                    {"default_headers": config.EXTRA_HEADERS}
                    if config.EXTRA_HEADERS
                    else {}
                ),
            }
        ],
            "temperature": config.MODEL_TEMPERATURE,
        }

        self.planner_llm_config = {
            "config_list": [
            {
                "model": config.TASK_MODEL_ID,
                "base_url": config.LLM_API_BASE,
                "api_type": "openai",
                "api_key": config.LLM_API_KEY,
                "response_format": Plan,
                **(
                    {"default_headers": config.EXTRA_HEADERS}
                    if config.EXTRA_HEADERS
                    else {}
                ),
            }
        ],
            "temperature": config.MODEL_TEMPERATURE,
        }

        self.reflection_llm_config = {
            "config_list": [
            {
                "model": config.TASK_MODEL_ID,
                "base_url": config.LLM_API_BASE,
                "api_type": "openai",
                "api_key": config.LLM_API_KEY,
                "response_format": Reflection,
                **(
                    {"default_headers": config.EXTRA_HEADERS}
                    if config.EXTRA_HEADERS
                    else {}
                ),
            }
        ],
            "temperature": config.MODEL_TEMPERATURE,
        }
