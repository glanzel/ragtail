from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from ..images.models import Image
from ..images.renditions import SourceImageIOError
from ..images.upload import create_image_from_upload, delete_image, update_image_focal_point
from ..images.fields import sanitize_upload_filename
from ..models import User
from .components.images import (
    ImageChooserPage,
    ImageEditPage,
    ImageListPage,
    ImageUploadPage,
)
from .deps import require_user
from .render import html_response


async def get_image_or_404(image_id: int) -> Image:
    image = await Image.objects.get_or_none(id=image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


def register_image_routes(router: APIRouter) -> None:
    @router.get("/images/")
    async def image_list(user: Annotated[User, Depends(require_user)]):
        images = await Image.objects.order_by("-created_at").all()
        return html_response(ImageListPage, username=user.username, images=images)

    @router.get("/images/upload/")
    async def image_upload_get(user: Annotated[User, Depends(require_user)]):
        return html_response(ImageUploadPage, username=user.username)

    @router.post("/images/upload/")
    async def image_upload_post(
        user: Annotated[User, Depends(require_user)],
        file: Annotated[UploadFile, File()],
        title: Annotated[str, Form()] = "",
    ):
        data = await file.read()
        if not data:
            return html_response(
                ImageUploadPage,
                username=user.username,
                error="Please choose an image file.",
            )
        filename = sanitize_upload_filename(file.filename or "upload.jpg")
        try:
            image = await create_image_from_upload(title=title or filename, filename=filename, data=data)
        except SourceImageIOError:
            return html_response(
                ImageUploadPage,
                username=user.username,
                error="Could not read the uploaded image.",
            )
        except Exception as exc:
            return html_response(
                ImageUploadPage,
                username=user.username,
                error=str(exc),
            )
        return RedirectResponse(f"/admin/images/{image.id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/images/chooser/")
    async def image_chooser(
        request: Request,
        user: Annotated[User, Depends(require_user)],
    ):
        field_name = request.query_params.get("field", "")
        images = await Image.objects.order_by("-created_at").all()
        return html_response(
            ImageChooserPage,
            username=user.username,
            images=images,
            field_name=field_name,
        )

    @router.get("/images/{image_id}/")
    async def image_detail(image_id: int, user: Annotated[User, Depends(require_user)]):
        image = await get_image_or_404(image_id)
        return RedirectResponse(f"/admin/images/{image.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/images/{image_id}/edit/")
    async def image_edit_get(image_id: int, user: Annotated[User, Depends(require_user)]):
        image = await get_image_or_404(image_id)
        return html_response(ImageEditPage, username=user.username, image=image)

    @router.post("/images/{image_id}/edit/")
    async def image_edit_post(
        image_id: int,
        user: Annotated[User, Depends(require_user)],
        title: Annotated[str, Form()],
        focal_point_x: Annotated[str, Form()] = "0.5",
        focal_point_y: Annotated[str, Form()] = "0.5",
    ):
        image = await get_image_or_404(image_id)
        image.title = title.strip() or image.title
        try:
            await update_image_focal_point(
                image,
                x=float(focal_point_x),
                y=float(focal_point_y),
            )
        except ValueError:
            return html_response(
                ImageEditPage,
                username=user.username,
                image=image,
                error="Invalid focal point coordinates.",
            )
        return RedirectResponse(f"/admin/images/{image.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/images/{image_id}/focal-point/")
    async def image_focal_get(image_id: int, user: Annotated[User, Depends(require_user)]):
        await get_image_or_404(image_id)
        return RedirectResponse(f"/admin/images/{image_id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/images/{image_id}/focal-point/")
    async def image_focal_post(
        image_id: int,
        user: Annotated[User, Depends(require_user)],
        focal_point_x: Annotated[str, Form()],
        focal_point_y: Annotated[str, Form()],
    ):
        image = await get_image_or_404(image_id)
        try:
            await update_image_focal_point(
                image,
                x=float(focal_point_x),
                y=float(focal_point_y),
            )
        except ValueError:
            return RedirectResponse(
                f"/admin/images/{image.id}/edit/",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        return RedirectResponse(f"/admin/images/{image.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/images/{image_id}/delete/")
    async def image_delete_post(image_id: int, user: Annotated[User, Depends(require_user)]):
        image = await get_image_or_404(image_id)
        await delete_image(image)
        return RedirectResponse("/admin/images/", status_code=status.HTTP_303_SEE_OTHER)
