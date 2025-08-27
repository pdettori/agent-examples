from pydantic import BaseModel, Field
from typing import Literal

############
# Pydantic types for LLM response formats
############

class Plan(BaseModel):
    steps: list[str]

class Reflection(BaseModel):
    decision: Literal['CONTINUE', 'TERMINATE'] = Field(
        description="If you determine that the goal can be completed, and you are providing the next step in the plan, select CONTINUE. If you determine that the plan cannot be accomplished, select TERMINATE")
    message: str = Field(description="Either the next step of the plan to follow, or if unable to accomplish goal, a specific explanation as to why.")