import re


HTML_PATTERN = re.compile(r"<[^>]+>")


def validate_text(data, field, required=True):
    value = data.get(field)
    if value is None:
        if required:
            raise ValueError(f"El campo '{field}' es obligatorio")
        return None

    value = str(value).strip()
    if required and not value:
        raise ValueError(f"El campo '{field}' no puede estar vacio")
    if value and HTML_PATTERN.search(value):
        raise ValueError(f"El campo '{field}' no puede contener HTML")
    return value if value else None
