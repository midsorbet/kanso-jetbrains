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


def _toward(color: str, target: str, other: str, minimum: float) -> str:
    """`color` moved toward `target` in 5% steps until it has `minimum` against `other`,
    or all the way."""
    step = 0.0
    while contrast(mix(color, target, step), other) < minimum and step < 1:
        step = min(1.0, step + 0.05)
    return mix(color, target, step)


def readable_pair(fg: str, bg: str, light: str, dark: str, minimum: float) -> tuple[str, str]:
    """Opaque `fg` and `bg` with at least `minimum` contrast.

    The foreground moves toward whichever of `light` and `dark` contrasts more with
    the background, which keeps its hue as long as possible. When even that color
    is not enough, the background moves toward the other one. Raises ValueError
    when `light` and `dark` themselves have less than `minimum`."""
    if contrast(fg, bg) >= minimum:
        return fg, bg
    if contrast(light, dark) < minimum:
        raise ValueError(f"{light} and {dark} have less than {minimum}:1")
    target, other = (light, dark) if contrast(light, bg) > contrast(dark, bg) else (dark, light)
    fg = _toward(fg, target, bg, minimum)
    if contrast(fg, bg) < minimum:
        bg = _toward(bg, other, fg, minimum)
    return fg, bg
