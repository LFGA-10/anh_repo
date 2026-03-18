from pydantic import BaseModel, Field
from typing import List, Optional

class TopicSchema(BaseModel):
    name: str = Field(..., description="The name of the topic")
    learning_outcomes: List[str] = Field(default_factory=list, description="List of learning outcomes for this topic")

class UnitSchema(BaseModel):
    id: str = Field(..., description="Unique ID for the unit (e.g., U1, U2)")
    name: str = Field(..., description="The name of the unit")
    topics: List[TopicSchema] = Field(default_factory=list, description="List of topics under this unit")

class CurriculumHierarchySchema(BaseModel):
    units: List[UnitSchema] = Field(default_factory=list, description="List of units in the module")

class DocumentCleaningSchema(BaseModel):
    cleaned_text: str = Field(..., description="The cleaned and fixed version of the raw text")
    hierarchy: CurriculumHierarchySchema = Field(..., description="The structured curriculum hierarchy found in the text")
    metadata_tags: List[str] = Field(default_factory=list, description="Key themes or tags identified in the content")
