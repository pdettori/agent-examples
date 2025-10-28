from pydantic import BaseModel, Field
from typing import Literal, Optional

############
# Pydantic types for LLM response formats
############

class IssueSearchInfo(BaseModel):
    owner: str = Field(None, description="The issue owner or organization.")
    repo: str = Field(None, description="The specified repository. Leave blank if none specified.")
    issue_numbers: list[int] = Field(None, description="Specific issue number(s) mentioned by the user. If none mentioned leave blank.")