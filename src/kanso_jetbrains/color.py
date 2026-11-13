"""Small sRGB helpers: parsing, mixing, alpha, and WCAG contrast."""


def rgb(color: str) -> tuple[int, int, int]:
    value = color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"expected #RRGGBB, got {color!r}")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def hex_color(red: float, green: float, blue: float) -> str:
    return "#" + "".join(f"{round(max(0, min(255, c))):02X}" for c in (red, green, blue))


def normalize(color: str) -> str:
    return hex_color(*rgb(color))


def mix(color: str, other: str, amount: float) -> str:
    """Move `amount` (0..1) of the way from `color` to `other`."""
    a, b = rgb(color), rgb(other)
    return hex_color(*(x + (y - x) * amount for x, y in zip(a, b)))


def alpha(color: str, opacity: float) -> str:
    """#RRGGBBAA with the given opacity (0..1)."""
    return normalize(color) + f"{round(opacity * 255):02X}"


def luminance(color: str) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(foreground: str, background: str) -> float:
    a, b = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)
