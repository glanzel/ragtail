from __future__ import annotations

import pyjsx.auto_setup  # noqa: F401
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from ..auth import (
    authenticate_user,
    change_password_error,
    create_user,
    email_error,
    normalize_email,
    reset_password_error,
    reset_user_password,
    update_user,
)
from ..images.models import Image
from ..richtext import prepare_body_for_storage
from ..seo import normalize_search_description, search_description_error
from ..menus import create_menu, create_menu_item
from ..models import Locale, Page, User
from ..pages import create_translation
from ..routing import get_locale
from ..sites import get_site_for_locale, is_tree_root, page_admin_title
from .components.dashboard import DashboardPage
from .components.locales import LocaleAddPage, LocaleEditPage, LocaleListPage
from .components.login import LoginPage
from .components.password_reset import ForgotPasswordPage
from .components.menus import MenuAddPage, MenuDetailPage, MenuEditPage, MenuListPage
from .components.users import (
    ChangePasswordPage,
    UserAddPage,
    UserEditPage,
    UserListPage,
    UserResetPasswordPage,
)
from .components.sites import SiteEditPage, SiteListPage
from .components.pages import (
    DeletePagePage,
    PageFormPage,
    PageListingPage,
    PageTypeChooserPage,
    TranslatePageForm,
)
from ..page_types import (
    cast_page,
    content_type_to_label,
    get_content_type,
    get_default_page_model,
    get_page_form_fields_for,
    get_page_model,
    get_page_model_or_404,
    get_page_type_choices,
    uses_richtext_for,
)
from .registry import PageFormField, get_page_form_fields, uses_richtext
from .images_router import register_image_routes
from .render import html_response
from .services import (
    Breadcrumb,
    build_breadcrumbs,
    build_page_tree,
    create_child_page,
    create_locale,
    delete_page,
    ensure_root_page,
    ensure_site_setup,
    ensure_tree_root,
    get_admin_locale,
    get_all_locales,
    get_all_sites,
    get_child_pages,
    get_locale_or_404,
    get_pages_for_site_root_choice,
    get_site_or_404,
    get_explorer_root_listing,
    get_locales_missing_translation,
    get_menu_item_or_404,
    get_menu_items,
    get_menu_or_404,
    get_menus_for_locale,
    get_missing_translations_by_page,
    get_all_users,
    get_user_by_email,
    get_user_or_404,
    can_delete_user,
    count_active_staff_users,
    validate_user_update,
    get_page_locale,
    get_page_or_404,
    get_page_public_url,
    get_pages_for_locale,
    resolve_page_for_admin_locale,
    resolve_translated_parent,
    set_admin_locale,
    update_locale,
    update_menu,
    update_page,
    update_site,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
from .deps import AdminLoginRequired, SESSION_USER_KEY, get_optional_user, require_user


def _login_url(next_path: str) -> str:
    return f"/admin/login/?next={quote(next_path, safe='/')}"


def _resolved_content_type(
    page: Page | None = None,
    *,
    content_type: str | None = None,
) -> str:
    if content_type:
        return content_type
    if page is not None and page.content_type:
        return page.content_type
    page_types = get_page_type_choices()
    if page_types:
        return page_types[0][0]
    return get_content_type(get_default_page_model())


def _form_fields_for(
    page: Page | None = None,
    *,
    content_type: str | None = None,
) -> list[PageFormField]:
    resolved = _resolved_content_type(page, content_type=content_type)
    model_fields = get_page_form_fields_for(resolved) if get_page_model(resolved) is not Page else []
    manual_fields = get_page_form_fields()
    if not model_fields:
        return manual_fields
    names = {field.name for field in model_fields}
    return model_fields + [field for field in manual_fields if field.name not in names]


def _registered_field_names(
    page: Page | None = None,
    *,
    content_type: str | None = None,
) -> set[str]:
    return {field.name for field in _form_fields_for(page, content_type=content_type)}


def _form_values(
    page: Page | None = None,
    *,
    content_type: str | None = None,
    **overrides,
) -> dict:
    resolved = _resolved_content_type(page, content_type=content_type)
    values = {
        "title": page.title if page else "",
        "slug": page.slug if page else "",
        "seo_title": page.seo_title or "" if page else "",
        "search_description": page.search_description or "" if page else "",
        "live": page.live if page else False,
        "show_in_menus": page.show_in_menus if page else False,
    }
    for field in _form_fields_for(page, content_type=resolved):
        attr_value = getattr(page, field.name, None) if page is not None else None
        if field.widget == "image":
            if isinstance(attr_value, Image) and attr_value.id is not None:
                values[field.name] = str(attr_value.id)
            else:
                values[field.name] = str(attr_value) if attr_value else ""
        else:
            values[field.name] = attr_value or ""
    values.update(overrides)
    return values


def _field_value_for_save(
    field: PageFormField,
    raw_value: str,
    *,
    page: Page | None,
) -> object:
    if field.widget == "image":
        cleaned = raw_value.strip()
        if not cleaned:
            return None
        return int(cleaned) if cleaned.isdigit() else None
    if field.widget == "richtext":
        return prepare_body_for_storage(raw_value)
    if field.name == "body" and field.name not in _registered_field_names(page):
        return getattr(page, "body", None) if page is not None else None
    return raw_value or None


def _extra_fields_from_form(
    form_data,
    *,
    page: Page | None = None,
    content_type: str | None = None,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for field in _form_fields_for(page, content_type=content_type):
        raw_value = str(form_data.get(field.name, ""))
        values[field.name] = _field_value_for_save(field, raw_value, page=page)
    return values


def _body_value_for_save(
    *,
    page: Page | None,
    submitted_body: str,
    content_type: str | None = None,
) -> str | None:
    if "body" not in _registered_field_names(page, content_type=content_type):
        return getattr(page, "body", None) if page is not None else None
    return prepare_body_for_storage(submitted_body)


def _image_field_previews(
    page: Page | None = None,
    *,
    content_type: str | None = None,
) -> dict[str, dict[str, str]]:
    previews: dict[str, dict[str, str]] = {}
    for field in _form_fields_for(page, content_type=content_type):
        if field.widget != "image":
            continue
        image = getattr(page, field.name, None) if page is not None else None
        if isinstance(image, Image) and image.id is not None:
            previews[field.name] = {
                "url": image.url,
                "title": image.title,
            }
    return previews


def _page_form_kwargs(
    page: Page | None = None,
    *,
    content_type: str | None = None,
) -> dict:
    resolved = _resolved_content_type(page, content_type=content_type)
    page_model = get_page_model(resolved)
    show_type = page_model is not Page
    extra_fields = _form_fields_for(page, content_type=resolved)
    return {
        "extra_fields": extra_fields,
        "include_richtext_script": uses_richtext_for(resolved) or uses_richtext(),
        "include_image_field_script": any(field.widget == "image" for field in extra_fields),
        "image_previews": _image_field_previews(page, content_type=resolved),
        "selected_content_type": resolved if show_type else None,
        "content_type_label": content_type_to_label(page_model) if show_type else None,
    }


def create_admin_router() -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.get("/login/")
    async def login_get(request: Request, next: str = "/admin/"):
        if await get_optional_user(request) is not None:
            return RedirectResponse(next, status_code=status.HTTP_303_SEE_OTHER)
        return html_response(LoginPage, next_url=next)

    @router.post("/login/")
    async def login_post(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        next: Annotated[str, Form()] = "/admin/",
    ):
        user = await authenticate_user(username, password)
        if user is None:
            return html_response(LoginPage, error="Invalid username or password.", next_url=next)
        request.session[SESSION_USER_KEY] = user.id
        return RedirectResponse(next or "/admin/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/logout/")
    async def logout_post(request: Request):
        request.session.clear()
        return RedirectResponse("/admin/login/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/password-reset/")
    async def password_reset_get():
        return html_response(ForgotPasswordPage)

    @router.get("/account/password/")
    async def account_password_get(user: Annotated[User, Depends(require_user)]):
        return html_response(ChangePasswordPage, username=user.username)

    @router.post("/account/password/")
    async def account_password_post(
        user: Annotated[User, Depends(require_user)],
        current_password: Annotated[str, Form()],
        password: Annotated[str, Form()],
        password_confirm: Annotated[str, Form()],
    ):
        error = change_password_error(
            user,
            current_password=current_password,
            new_password=password,
            confirm_password=password_confirm,
        )
        if error:
            return html_response(ChangePasswordPage, username=user.username, error=error)
        await reset_user_password(user, password=password)
        return html_response(
            ChangePasswordPage,
            username=user.username,
            success="Your password has been changed.",
        )

    @router.post("/set-locale/")
    async def set_locale_post(
        request: Request,
        user: Annotated[User, Depends(require_user)],
        language_code: Annotated[str, Form()],
        next: Annotated[str, Form()] = "/admin/",
    ):
        locale = await get_locale(language_code.strip().lower())
        if locale is not None and locale.is_active:
            set_admin_locale(request, locale)
        return RedirectResponse(next or "/admin/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/")
    async def dashboard(request: Request, user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale(request)
        page_count = len(await Page.objects.filter(locale_id=locale.id).all())
        return html_response(
            DashboardPage,
            username=user.username,
            page_count=page_count,
            locale_name=locale.display_name,
        )

    @router.get("/locales/")
    async def locales_list(user: Annotated[User, Depends(require_user)]):
        locales = await get_all_locales()
        return html_response(LocaleListPage, username=user.username, locales=locales)

    @router.get("/locales/add/")
    async def locales_add_get(user: Annotated[User, Depends(require_user)]):
        return html_response(LocaleAddPage, username=user.username, values=_form_values())

    @router.post("/locales/add/")
    async def locales_add_post(
        user: Annotated[User, Depends(require_user)],
        language_code: Annotated[str, Form()],
        display_name: Annotated[str, Form()],
        is_default: Annotated[str | None, Form()] = None,
    ):
        values = {
            "language_code": language_code,
            "display_name": display_name,
            "is_default": is_default == "1",
        }
        code = language_code.strip().lower()
        if not code or not display_name.strip():
            return html_response(
                LocaleAddPage,
                username=user.username,
                values=values,
                error="Language code and display name are required.",
            )
        existing = await get_all_locales()
        if any(locale.language_code == code for locale in existing):
            return html_response(
                LocaleAddPage,
                username=user.username,
                values=values,
                error=f"Locale '{code}' already exists.",
            )
        locale = await create_locale(
            language_code=code,
            display_name=display_name.strip(),
            is_default=is_default == "1" or not existing,
        )
        await ensure_site_setup(locale)
        return RedirectResponse("/admin/locales/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/locales/{locale_id}/edit/")
    async def locales_edit_get(locale_id: int, user: Annotated[User, Depends(require_user)]):
        locale = await get_locale_or_404(locale_id)
        return html_response(LocaleEditPage, username=user.username, locale=locale)

    @router.post("/locales/{locale_id}/edit/")
    async def locales_edit_post(
        locale_id: int,
        user: Annotated[User, Depends(require_user)],
        display_name: Annotated[str, Form()],
        is_default: Annotated[str | None, Form()] = None,
        is_active: Annotated[str | None, Form()] = None,
    ):
        locale = await get_locale_or_404(locale_id)
        values = {
            "display_name": display_name,
            "is_default": is_default == "1",
            "is_active": is_active == "1",
        }
        if not display_name.strip():
            return html_response(
                LocaleEditPage,
                username=user.username,
                locale=locale,
                values=values,
                error="Display name is required.",
            )
        try:
            await update_locale(
                locale,
                display_name=display_name,
                is_default=is_default == "1",
                is_active=is_active == "1",
            )
        except ValueError as exc:
            return html_response(
                LocaleEditPage,
                username=user.username,
                locale=locale,
                values=values,
                error=str(exc),
            )
        return RedirectResponse("/admin/locales/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/users/")
    async def users_list(user: Annotated[User, Depends(require_user)]):
        users = await get_all_users()
        return html_response(
            UserListPage,
            username=user.username,
            users=users,
            current_user_id=user.id,
        )

    @router.get("/users/add/")
    async def users_add_get(user: Annotated[User, Depends(require_user)]):
        return html_response(
            UserAddPage,
            username=user.username,
            values={"is_active": True, "is_staff": True},
        )

    @router.post("/users/add/")
    async def users_add_post(
        user: Annotated[User, Depends(require_user)],
        username: Annotated[str, Form()],
        email: Annotated[str, Form()],
        password: Annotated[str, Form()],
        is_staff: Annotated[str | None, Form()] = None,
        is_active: Annotated[str | None, Form()] = None,
    ):
        values = {
            "username": username,
            "email": email,
            "is_staff": is_staff == "1",
            "is_active": is_active == "1",
        }
        clean_username = username.strip()
        if not clean_username or not password:
            return html_response(
                UserAddPage,
                username=user.username,
                values=values,
                error="Username and password are required.",
            )
        validation_error = email_error(email)
        if validation_error:
            return html_response(
                UserAddPage,
                username=user.username,
                values=values,
                error=validation_error,
            )
        existing = await User.objects.get_or_none(username=clean_username)
        if existing is not None:
            return html_response(
                UserAddPage,
                username=user.username,
                values=values,
                error=f"Username '{clean_username}' is already taken.",
            )
        existing_email = await get_user_by_email(email)
        if existing_email is not None:
            return html_response(
                UserAddPage,
                username=user.username,
                values=values,
                error=f"Email '{normalize_email(email)}' is already in use.",
            )
        await create_user(
            username=clean_username,
            email=email,
            password=password,
            is_staff=is_staff == "1",
            is_active=is_active == "1",
        )
        return RedirectResponse("/admin/users/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/users/{user_id}/edit/")
    async def users_edit_get(user_id: int, user: Annotated[User, Depends(require_user)]):
        target = await get_user_or_404(user_id)
        can_delete, _ = await can_delete_user(target=target, actor=user)
        return html_response(
            UserEditPage,
            username=user.username,
            user=target,
            current_user_id=user.id,
            can_delete=can_delete,
        )

    @router.get("/users/{user_id}/reset-password/")
    async def users_reset_password_get(
        user_id: int,
        user: Annotated[User, Depends(require_user)],
    ):
        target = await get_user_or_404(user_id)
        return html_response(
            UserResetPasswordPage,
            username=user.username,
            user=target,
        )

    @router.post("/users/{user_id}/reset-password/")
    async def users_reset_password_post(
        user_id: int,
        user: Annotated[User, Depends(require_user)],
        password: Annotated[str, Form()],
        password_confirm: Annotated[str, Form()],
    ):
        target = await get_user_or_404(user_id)
        error = reset_password_error(password=password, confirm_password=password_confirm)
        if error:
            return html_response(
                UserResetPasswordPage,
                username=user.username,
                user=target,
                error=error,
            )
        await reset_user_password(target, password=password)
        return html_response(
            UserResetPasswordPage,
            username=user.username,
            user=target,
            success=f"Password for '{target.username}' has been reset.",
        )

    @router.post("/users/{user_id}/edit/")
    async def users_edit_post(
        user_id: int,
        user: Annotated[User, Depends(require_user)],
        email: Annotated[str, Form()],
        is_staff: Annotated[str | None, Form()] = None,
        is_active: Annotated[str | None, Form()] = None,
    ):
        target = await get_user_or_404(user_id)
        is_staff_value = target.is_staff if target.id == user.id else is_staff == "1"
        is_active_value = target.is_active if target.id == user.id else is_active == "1"
        values = {
            "email": email,
            "is_staff": is_staff_value,
            "is_active": is_active_value,
        }
        email_validation_error = email_error(email)
        if email_validation_error:
            can_delete, _ = await can_delete_user(target=target, actor=user)
            return html_response(
                UserEditPage,
                username=user.username,
                user=target,
                current_user_id=user.id,
                values=values,
                error=email_validation_error,
                can_delete=can_delete,
            )
        existing_email = await get_user_by_email(email)
        if existing_email is not None and existing_email.id != target.id:
            can_delete, _ = await can_delete_user(target=target, actor=user)
            return html_response(
                UserEditPage,
                username=user.username,
                user=target,
                current_user_id=user.id,
                values=values,
                error=f"Email '{normalize_email(email)}' is already in use.",
                can_delete=can_delete,
            )
        validation_error = await validate_user_update(
            target=target,
            actor=user,
            is_active=is_active_value,
            is_staff=is_staff_value,
        )
        if validation_error:
            can_delete, _ = await can_delete_user(target=target, actor=user)
            return html_response(
                UserEditPage,
                username=user.username,
                user=target,
                current_user_id=user.id,
                values=values,
                error=validation_error,
                can_delete=can_delete,
            )
        if not is_staff_value and target.is_active and target.is_staff:
            remaining = await count_active_staff_users(exclude_user_id=target.id)
            if remaining == 0:
                can_delete, _ = await can_delete_user(target=target, actor=user)
                return html_response(
                    UserEditPage,
                    username=user.username,
                    user=target,
                    current_user_id=user.id,
                    values=values,
                    error="At least one active staff user is required.",
                    can_delete=can_delete,
                )
        await update_user(
            target,
            email=email,
            is_active=is_active_value,
            is_staff=is_staff_value,
        )
        return RedirectResponse("/admin/users/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/users/{user_id}/delete/")
    async def users_delete_post(
        user_id: int,
        user: Annotated[User, Depends(require_user)],
    ):
        target = await get_user_or_404(user_id)
        can_delete, error = await can_delete_user(target=target, actor=user)
        if not can_delete:
            return html_response(
                UserEditPage,
                username=user.username,
                user=target,
                current_user_id=user.id,
                error=error,
                can_delete=False,
            )
        await target.delete()
        return RedirectResponse("/admin/users/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/menus/")
    async def menus_list(request: Request, user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale(request)
        menus = await get_menus_for_locale(locale)
        locales = await get_all_locales()
        return html_response(
            MenuListPage,
            username=user.username,
            menus=menus,
            locales=locales,
            current_locale=locale,
            return_url="/admin/menus/",
        )

    @router.get("/menus/add/")
    async def menus_add_get(user: Annotated[User, Depends(require_user)]):
        return html_response(
            MenuAddPage,
            username=user.username,
            values={"is_active": True},
        )

    @router.post("/menus/add/")
    async def menus_add_post(
        request: Request,
        user: Annotated[User, Depends(require_user)],
        name: Annotated[str, Form()],
        slug: Annotated[str, Form()],
        is_active: Annotated[str | None, Form()] = None,
    ):
        locale = await get_admin_locale(request)
        values = {"name": name, "slug": slug, "is_active": is_active == "1"}
        if not name.strip() or not slug.strip():
            return html_response(
                MenuAddPage,
                username=user.username,
                values=values,
                error="Name and slug are required.",
            )
        menu = await create_menu(
            name=name.strip(),
            slug=slug.strip().lower(),
            locale=locale,
            is_active=is_active == "1",
        )
        return RedirectResponse(f"/admin/menus/{menu.id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/menus/{menu_id}/")
    async def menus_detail(menu_id: int, user: Annotated[User, Depends(require_user)]):
        menu = await get_menu_or_404(menu_id)
        menu_locale = await get_locale_or_404(menu.locale_id) if menu.locale_id else await get_admin_locale()
        items = await get_menu_items(menu)
        pages = await get_pages_for_locale(menu_locale)
        return html_response(
            MenuDetailPage,
            username=user.username,
            menu=menu,
            items=items,
            pages=pages,
        )

    @router.get("/menus/{menu_id}/edit/")
    async def menus_edit_get(menu_id: int, user: Annotated[User, Depends(require_user)]):
        menu = await get_menu_or_404(menu_id)
        return html_response(MenuEditPage, username=user.username, menu=menu)

    @router.post("/menus/{menu_id}/edit/")
    async def menus_edit_post(
        menu_id: int,
        user: Annotated[User, Depends(require_user)],
        name: Annotated[str, Form()],
        slug: Annotated[str, Form()],
        is_active: Annotated[str | None, Form()] = None,
    ):
        menu = await get_menu_or_404(menu_id)
        values = {"name": name, "slug": slug, "is_active": is_active == "1"}
        if not name.strip() or not slug.strip():
            return html_response(
                MenuEditPage,
                username=user.username,
                menu=menu,
                values=values,
                error="Name and slug are required.",
            )
        try:
            await update_menu(
                menu,
                name=name,
                slug=slug,
                is_active=is_active == "1",
            )
        except ValueError as exc:
            return html_response(
                MenuEditPage,
                username=user.username,
                menu=menu,
                values=values,
                error=str(exc),
            )
        return RedirectResponse(f"/admin/menus/{menu_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/menus/{menu_id}/items/add/")
    async def menus_item_add(
        menu_id: int,
        user: Annotated[User, Depends(require_user)],
        label: Annotated[str, Form()],
        page_id: Annotated[str, Form()] = "",
        url: Annotated[str, Form()] = "",
        sort_order: Annotated[str, Form()] = "0",
        open_in_new_tab: Annotated[str | None, Form()] = None,
    ):
        menu = await get_menu_or_404(menu_id)
        menu_locale = await get_locale_or_404(menu.locale_id) if menu.locale_id else await get_admin_locale()
        values = {
            "label": label,
            "page_id": page_id,
            "url": url,
            "sort_order": sort_order,
            "open_in_new_tab": open_in_new_tab == "1",
        }
        if not label.strip():
            return html_response(
                MenuDetailPage,
                username=user.username,
                menu=menu,
                items=await get_menu_items(menu),
                pages=await get_pages_for_locale(menu_locale),
                values=values,
                error="Label is required.",
            )
        page = None
        if page_id.strip():
            page = await get_page_or_404(int(page_id))
        elif not url.strip():
            return html_response(
                MenuDetailPage,
                username=user.username,
                menu=menu,
                items=await get_menu_items(menu),
                pages=await get_pages_for_locale(menu_locale),
                values=values,
                error="Choose a page or provide an external URL.",
            )
        await create_menu_item(
            menu=menu,
            label=label.strip(),
            page=page,
            url=url.strip() or None,
            sort_order=int(sort_order or 0),
            open_in_new_tab=open_in_new_tab == "1",
        )
        return RedirectResponse(f"/admin/menus/{menu_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/menus/items/{item_id}/delete/")
    async def menus_item_delete(item_id: int, user: Annotated[User, Depends(require_user)]):
        item = await get_menu_item_or_404(item_id)
        menu_id = item.menu_id
        await item.delete()
        return RedirectResponse(f"/admin/menus/{menu_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/sites/")
    async def sites_list(user: Annotated[User, Depends(require_user)]):
        sites = await get_all_sites()
        locales = {locale.id: locale for locale in await get_all_locales()}
        return html_response(
            SiteListPage,
            username=user.username,
            sites=sites,
            locales=locales,
        )

    @router.get("/sites/{site_id}/edit/")
    async def sites_edit_get(site_id: int, user: Annotated[User, Depends(require_user)]):
        site = await get_site_or_404(site_id)
        locale = await get_locale_or_404(site.locale_id) if site.locale_id else None
        if locale is None:
            raise HTTPException(status_code=404, detail="Locale not found")
        pages = await get_pages_for_site_root_choice(locale)
        return html_response(
            SiteEditPage,
            username=user.username,
            site=site,
            locale=locale,
            pages=pages,
        )

    @router.post("/sites/{site_id}/edit/")
    async def sites_edit_post(
        site_id: int,
        user: Annotated[User, Depends(require_user)],
        hostname: Annotated[str, Form()],
        port: Annotated[int, Form()],
        site_name: Annotated[str, Form()] = "",
        root_page_id: Annotated[str, Form()] = "",
        is_default_site: Annotated[str | None, Form()] = None,
    ):
        site = await get_site_or_404(site_id)
        locale = await get_locale_or_404(site.locale_id) if site.locale_id else None
        if locale is None:
            raise HTTPException(status_code=404, detail="Locale not found")
        pages = await get_pages_for_site_root_choice(locale)
        values = {
            "hostname": hostname,
            "port": port,
            "site_name": site_name,
            "root_page_id": root_page_id,
            "is_default_site": is_default_site == "1",
        }
        parsed_root_page_id = int(root_page_id) if root_page_id.strip() else None
        try:
            await update_site(
                site,
                hostname=hostname,
                port=port,
                site_name=site_name or None,
                root_page_id=parsed_root_page_id,
                is_default_site=is_default_site == "1",
            )
        except ValueError as exc:
            return html_response(
                SiteEditPage,
                username=user.username,
                site=site,
                locale=locale,
                pages=pages,
                values=values,
                error=str(exc),
            )
        return RedirectResponse("/admin/sites/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/")
    async def pages_root(request: Request, user: Annotated[User, Depends(require_user)]):
        admin_locale = await get_admin_locale(request)
        tree_root, children = await get_explorer_root_listing(admin_locale)
        tree = await build_page_tree(admin_locale)
        locales = await get_all_locales()
        missing_by_child = await get_missing_translations_by_page(children)
        site = await get_site_for_locale(admin_locale)
        return html_response(
            PageListingPage,
            username=user.username,
            parent_page=None,
            children=children,
            tree=tree,
            locales=locales,
            current_locale=admin_locale,
            missing_by_child=missing_by_child,
            parent_missing_locales=[],
            breadcrumbs=[Breadcrumb(title="Pages", url="/admin/pages/")],
            is_explorer_root=True,
            add_parent_id=tree_root.id,
            site=site,
        )

    @router.get("/pages/add/")
    async def page_add_get(
        request: Request,
        user: Annotated[User, Depends(require_user)],
        parent: int | None = None,
        content_type: str | None = None,
    ):
        default_locale = await get_admin_locale(request)
        parent_page = (
            await get_page_or_404(parent)
            if parent
            else await ensure_tree_root(default_locale)
        )
        breadcrumbs = await build_breadcrumbs(parent_page)
        breadcrumbs.append(type(breadcrumbs[-1])("Add child page", None))

        parent_label = page_admin_title(parent_page)
        page_types = get_page_type_choices()
        if page_types and content_type is None:
            if len(page_types) == 1:
                content_type = page_types[0][0]
            else:
                breadcrumbs[-1] = type(breadcrumbs[-1])("Choose page type", None)
                return html_response(
                    PageTypeChooserPage,
                    username=user.username,
                    parent_page=parent_page,
                    parent_label=parent_label,
                    breadcrumbs=breadcrumbs,
                    page_types=page_types,
                )

        resolved_content_type = _resolved_content_type(content_type=content_type)
        page_model = get_page_model(resolved_content_type)
        if page_types and page_model is Page:
            raise HTTPException(status_code=404, detail=f"Page type '{resolved_content_type}' is not registered")

        parent_label = page_admin_title(parent_page)
        parent_form_extras = {
            "parent_label": parent_label,
            "parent_cancel_href": (
                "/admin/pages/" if is_tree_root(parent_page) else f"/admin/pages/{parent_page.id}/"
            ),
        }
        return html_response(
            PageFormPage,
            username=user.username,
            parent_page=parent_page,
            breadcrumbs=breadcrumbs,
            action_url=f"/admin/pages/add/?parent={parent_page.id}",
            title="Add child page",
            submit_label="Create page",
            values=_form_values(content_type=resolved_content_type),
            **parent_form_extras,
            **_page_form_kwargs(content_type=resolved_content_type),
        )

    @router.post("/pages/add/")
    async def page_add_post(
        request: Request,
        user: Annotated[User, Depends(require_user)],
        parent: int | None = None,
    ):
        form = await request.form()
        title = str(form.get("title", ""))
        slug = str(form.get("slug", ""))
        seo_title = str(form.get("seo_title", ""))
        search_description = str(form.get("search_description", ""))
        live = form.get("live")
        show_in_menus = form.get("show_in_menus")
        content_type = str(form.get("content_type", "") or _resolved_content_type())

        default_locale = await get_admin_locale(request)
        parent_page = (
            await get_page_or_404(parent)
            if parent
            else await ensure_tree_root(default_locale)
        )
        locale = await get_page_locale(parent_page)
        page_types = get_page_type_choices()
        try:
            page_model = (
                get_page_model_or_404(content_type)
                if page_types
                else get_default_page_model()
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        breadcrumbs = await build_breadcrumbs(parent_page)
        breadcrumbs.append(type(breadcrumbs[-1])("Add child page", None))
        parent_label = page_admin_title(parent_page)
        extra_fields = _extra_fields_from_form(form, content_type=content_type)
        values = _form_values(
            None,
            content_type=content_type,
            title=title,
            slug=slug,
            seo_title=seo_title,
            search_description=search_description,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            **{name: value or "" for name, value in extra_fields.items()},
        )
        form_kwargs = {
            **_page_form_kwargs(content_type=content_type),
        }
        parent_form_extras = {
            "parent_label": parent_label,
            "parent_cancel_href": (
                "/admin/pages/" if is_tree_root(parent_page) else f"/admin/pages/{parent_page.id}/"
            ),
        }
        if not title.strip():
            return html_response(
                PageFormPage,
                username=user.username,
                parent_page=parent_page,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/add/?parent={parent_page.id}",
                title="Add child page",
                submit_label="Create page",
                values=values,
                error="Title is required.",
                **parent_form_extras,
                **form_kwargs,
            )
        if error := search_description_error(search_description):
            return html_response(
                PageFormPage,
                username=user.username,
                parent_page=parent_page,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/add/?parent={parent_page.id}",
                title="Add child page",
                submit_label="Create page",
                values=values,
                error=error,
                **parent_form_extras,
                **form_kwargs,
            )
        page = await create_child_page(
            parent=parent_page,
            title=title.strip(),
            slug=slug,
            locale=locale,
            page_model=page_model if page_types else None,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            seo_title=seo_title or None,
            search_description=normalize_search_description(search_description),
            **extra_fields,
        )
        return RedirectResponse(f"/admin/pages/{page.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/{page_id}/translate/")
    async def page_translate_get(
        page_id: int,
        user: Annotated[User, Depends(require_user)],
        language_code: str,
    ):
        source_page = await get_page_or_404(page_id)
        target_locale = await get_locale(language_code.strip().lower())
        if target_locale is None:
            raise HTTPException(status_code=404, detail="Locale not found")
        existing = None
        if source_page.translation_key:
            existing = await Page.objects.filter(
                translation_key=source_page.translation_key,
                locale_id=target_locale.id,
            ).first()
        if existing is not None:
            return RedirectResponse(f"/admin/pages/{existing.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)
        breadcrumbs = await build_breadcrumbs(source_page)
        breadcrumbs.append(type(breadcrumbs[-1])(f"Translate ({target_locale.language_code})", None))
        return html_response(
            TranslatePageForm,
            username=user.username,
            source_page=source_page,
            target_locale=target_locale,
            breadcrumbs=breadcrumbs,
            action_url=f"/admin/pages/{page_id}/translate/?language_code={target_locale.language_code}",
            values={"title": source_page.title, "slug": source_page.slug, "live": source_page.live},
        )

    @router.post("/pages/{page_id}/translate/")
    async def page_translate_post(
        page_id: int,
        user: Annotated[User, Depends(require_user)],
        language_code: str,
        title: Annotated[str, Form()],
        slug: Annotated[str, Form()] = "",
        live: Annotated[str | None, Form()] = None,
    ):
        source_page = await get_page_or_404(page_id)
        target_locale = await get_locale(language_code.strip().lower())
        if target_locale is None:
            raise HTTPException(status_code=404, detail="Locale not found")
        breadcrumbs = await build_breadcrumbs(source_page)
        breadcrumbs.append(type(breadcrumbs[-1])(f"Translate ({target_locale.language_code})", None))
        values = {"title": title, "slug": slug, "live": live == "1"}
        if not title.strip():
            return html_response(
                TranslatePageForm,
                username=user.username,
                source_page=source_page,
                target_locale=target_locale,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/{page_id}/translate/?language_code={target_locale.language_code}",
                values=values,
                error="Title is required.",
            )
        if source_page.translation_key:
            existing = await Page.objects.filter(
                translation_key=source_page.translation_key,
                locale_id=target_locale.id,
            ).first()
            if existing is not None:
                return RedirectResponse(f"/admin/pages/{existing.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)
        parent = await resolve_translated_parent(source_page, target_locale)
        translated = await create_translation(
            source_page,
            title=title.strip(),
            slug=slug,
            locale=target_locale,
            parent=parent,
            live=live == "1",
        )
        return RedirectResponse(f"/admin/pages/{translated.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/{page_id}/")
    async def page_listing(
        request: Request,
        page_id: int,
        user: Annotated[User, Depends(require_user)],
    ):
        admin_locale = await get_admin_locale(request)
        page = await get_page_or_404(page_id)
        if is_tree_root(page):
            return RedirectResponse("/admin/pages/", status_code=status.HTTP_303_SEE_OTHER)
        page_in_locale = await resolve_page_for_admin_locale(page, admin_locale)
        if page_in_locale.id != page.id:
            return RedirectResponse(
                f"/admin/pages/{page_in_locale.id}/",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        children = await get_child_pages(page)
        tree = await build_page_tree(admin_locale)
        locales = await get_all_locales()
        breadcrumbs = await build_breadcrumbs(page)
        missing_by_child = await get_missing_translations_by_page(children)
        parent_missing = await get_locales_missing_translation(page)
        site = await get_site_for_locale(admin_locale)
        public_url = await get_page_public_url(page)
        return html_response(
            PageListingPage,
            username=user.username,
            parent_page=page,
            children=children,
            tree=tree,
            locales=locales,
            current_locale=admin_locale,
            missing_by_child=missing_by_child,
            parent_missing_locales=parent_missing,
            breadcrumbs=breadcrumbs,
            site=site,
            public_url=public_url,
        )

    @router.get("/pages/{page_id}/edit/")
    async def page_edit_get(page_id: int, user: Annotated[User, Depends(require_user)]):
        page = await cast_page(await get_page_or_404(page_id))
        if is_tree_root(page):
            raise HTTPException(status_code=404, detail="The technical tree root cannot be edited.")
        breadcrumbs = await build_breadcrumbs(page)
        breadcrumbs.append(type(breadcrumbs[-1])("Edit", None))
        public_url = await get_page_public_url(page)
        return html_response(
            PageFormPage,
            username=user.username,
            page=page,
            breadcrumbs=breadcrumbs,
            action_url=f"/admin/pages/{page_id}/edit/",
            title=f"Editing {page.title}",
            submit_label="Save draft",
            values=_form_values(page),
            public_url=public_url,
            **_page_form_kwargs(page),
        )

    @router.post("/pages/{page_id}/edit/")
    async def page_edit_post(
        request: Request,
        page_id: int,
        user: Annotated[User, Depends(require_user)],
    ):
        form = await request.form()
        title = str(form.get("title", ""))
        slug = str(form.get("slug", ""))
        seo_title = str(form.get("seo_title", ""))
        search_description = str(form.get("search_description", ""))
        live = form.get("live")
        show_in_menus = form.get("show_in_menus")

        page = await cast_page(await get_page_or_404(page_id))
        if is_tree_root(page):
            raise HTTPException(status_code=404, detail="The technical tree root cannot be edited.")
        breadcrumbs = await build_breadcrumbs(page)
        breadcrumbs.append(type(breadcrumbs[-1])("Edit", None))
        extra_fields = _extra_fields_from_form(form, page=page)
        values = _form_values(
            page,
            title=title,
            slug=slug,
            seo_title=seo_title,
            search_description=search_description,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            **{name: value or "" for name, value in extra_fields.items()},
        )
        form_kwargs = _page_form_kwargs(page)
        public_url = await get_page_public_url(page)
        if not title.strip():
            return html_response(
                PageFormPage,
                username=user.username,
                page=page,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/{page_id}/edit/",
                title=f"Editing {page.title}",
                submit_label="Save draft",
                values=values,
                error="Title is required.",
                public_url=public_url,
                **form_kwargs,
            )
        if error := search_description_error(search_description):
            return html_response(
                PageFormPage,
                username=user.username,
                page=page,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/{page_id}/edit/",
                title=f"Editing {page.title}",
                submit_label="Save draft",
                values=values,
                error=error,
                public_url=public_url,
                **form_kwargs,
            )
        await update_page(
            page,
            title=title.strip(),
            slug=slug,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            seo_title=seo_title or None,
            search_description=normalize_search_description(search_description),
            **extra_fields,
        )
        return RedirectResponse(f"/admin/pages/{page_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/{page_id}/delete/")
    async def page_delete_get(page_id: int, user: Annotated[User, Depends(require_user)]):
        page = await get_page_or_404(page_id)
        if is_tree_root(page):
            raise HTTPException(status_code=404, detail="The technical tree root cannot be deleted.")
        breadcrumbs = await build_breadcrumbs(page)
        breadcrumbs.append(type(breadcrumbs[-1])("Delete", None))
        return html_response(
            DeletePagePage,
            username=user.username,
            page=page,
            breadcrumbs=breadcrumbs,
        )

    @router.post("/pages/{page_id}/delete/")
    async def page_delete_post(
        request: Request,
        page_id: int,
        user: Annotated[User, Depends(require_user)],
    ):
        page = await get_page_or_404(page_id)
        if is_tree_root(page):
            raise HTTPException(status_code=404, detail="The technical tree root cannot be deleted.")
        parent_id = page.parent_id
        try:
            await delete_page(page)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if parent_id:
            parent = await get_page_or_404(parent_id)
            if is_tree_root(parent):
                return RedirectResponse("/admin/pages/", status_code=status.HTTP_303_SEE_OTHER)
            return RedirectResponse(f"/admin/pages/{parent_id}/", status_code=status.HTTP_303_SEE_OTHER)
        return RedirectResponse("/admin/pages/", status_code=status.HTTP_303_SEE_OTHER)

    register_image_routes(router)

    return router
