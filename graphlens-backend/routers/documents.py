"""Document upload / list / delete endpoints. Implemented in Phase 4."""
from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])

# POST   /upload            -> Phase 1 + Phase 4
# GET    /documents         -> Phase 4
# DELETE /documents/{id}    -> Phase 4
