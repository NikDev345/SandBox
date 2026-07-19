from fastapi import APIRouter, Depends, HTTPException, status

from app.utils.auth import get_current_user
from app.models.blog_outline_generator import (
    BlogOutlineRequest,
    BlogOutlineResponse,
)
from app.models.user import Users
from app.services.blog_generator.blog_outline_generator import (
    BlogOutlineGeneratorService,
)

router = APIRouter(
    prefix="/blog-outline-generator",
    tags=["Blog Outline Generator"],
)


@router.post(
    "/generate",
    response_model=BlogOutlineResponse,
    summary="Generate a Blog Outline",
)
async def generate_blog_outline(
    request: BlogOutlineRequest,
    current_user: Users = Depends(get_current_user),
):
    """
    Generate a professional SEO-friendly blog outline using AI.
    """

    try:
        return await BlogOutlineGeneratorService.generate(request)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate blog outline: {str(e)}",
        )