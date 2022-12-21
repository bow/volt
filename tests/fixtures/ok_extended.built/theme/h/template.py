from volt import template


@template.filter
def pub_timestamp(meta: dict) -> str:
    if (pub_date := meta.get("pub_date")) is not None:
        return pub_date.strftime("%A, %d %B %Y")
    return ""


@template.filter(name="basename")
def get_base_name(url: str) -> str:
    return url.removeprefix("/").removesuffix(".html")


@template.test
def is_index(meta: dict) -> bool:
    return (meta.get("url") or "") == "/index.html"
