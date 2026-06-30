# Images

Ragtail provides a Wagtail-inspired image library with focal points, cached renditions, and `ImageField` support on page models. Image processing via Pillow is included in the main package.

## Configuration

Configure media storage when creating the CMS:

```python
from ragtail import FastAPICMS

cms = FastAPICMS(
    media_root="/var/www/media",
    media_url="/media/",
)
```

When mounting the CMS, public files are served from `MEDIA_URL`:

```python
cms.mount(app)  # mounts /media/ by default
```

Storage uses a protocol-based backend (`LocalStorage` today, S3-ready interface for later).

## Image model

Upload images via the admin **Images** section or programmatically:

```python
from ragtail.images import create_image_from_upload

image = await create_image_from_upload(
    title="Hero",
    filename="hero.jpg",
    data=file_bytes,
)
```

Each image stores width, height, optional focal point (`focal_point_x`, `focal_point_y` as 0.0–1.0), and generates cached **renditions** on demand:

```python
rendition = await image.get_rendition("fill-800x450|format-webp")
print(rendition.url, rendition.width, rendition.height)
```

Supported filter operations (Wagtail-style):

- `width-N`, `height-N`
- `max-WxH`, `min-WxH`, `fill-WxH` (fill uses the focal point)
- `format-jpeg`, `format-webp`, `format-png`
- Combine with `|`, e.g. `fill-1200x480|format-webp`

## ImageField on pages

```python
from oxyde import Field
from ragtail import Image, ImageField, register_page_model
from ragtail.models import Page

@register_page_model
class BlogPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")
    hero_image: Image | None = ImageField(
        default=None,
        renditions=("fill-1200x480", "width-400"),
    )
```

Image references are stored in `page_data` as integer IDs and resolved automatically by `cast_page()`.

## Templates

### PyJSX

Use `get_context()` or precomputed renditions from `enrich_page_images()`:

```python
from ragtail.images.templates import resolve_rendition

async def get_context(self, request, route):
    hero = await resolve_rendition(self.hero_image, "fill-1200x480")
    return {"hero": hero}
```

In the component:

```python
<img src={hero.url} width={hero.width} height={hero.height} alt={hero.alt} />
```

### Jinja2

`Jinja2Renderer` registers `rendition()` and `ragtail_image()` helpers. Declare default renditions on `ImageField` or precompute in `get_context()`:

```html
{{ ragtail_image(page.hero_image, "fill-800x450", css_class="hero") }}

<img src="{{ hero_image_renditions['width-400'].url }}" alt="{{ page.hero_image.title }}">
```

### JSON API

- `GET /api/cms/images/{id}/` — image metadata
- `GET /api/cms/images/{id}/renditions/{filter_spec}/` — rendition URL and dimensions
- `GET /api/cms/pages/{path}` — includes `fields.hero_image` when present

## Admin

- **Images** — library grid, upload, edit title, delete
- **Focal point editor** — click the preview to set the crop centre for `fill-*` renditions
- **Page editor** — image chooser widget for `ImageField` properties

Rich-text inline images are not included in this iteration.
