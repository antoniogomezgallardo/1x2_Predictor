from pydantic import BaseModel
from typing import Optional


class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: Optional[str]
    logo: Optional[str]
    league_id: int
    founded: Optional[int]
    venue_name: Optional[str]
    
    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    api_id: int
    name: str
    short_name: Optional[str] = None
    logo: Optional[str] = None
    league_id: int
    founded: Optional[int] = None
    venue_name: Optional[str] = None
    venue_capacity: Optional[int] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    logo: Optional[str] = None
    founded: Optional[int] = None
    venue_name: Optional[str] = None
    venue_capacity: Optional[int] = None