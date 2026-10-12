"""HTTP routes."""
from fastapi import APIRouter

router = APIRouter(
    prefix="/cases",
    tags=["cases"]  
)

@router.get("/")
async def read_cases():
    ...

@router.get("/{case_id}")
async def read_case(case_id: int):
    ...

@router.post("/")
async def create_case(case: dict):
    ...