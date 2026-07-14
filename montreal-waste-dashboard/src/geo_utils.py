import re
import numpy as np


def normkey(s):
    s = str(s).replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-zà-ÿ]", "", s.lower())


def extract_rings(geom):
    if geom.geom_type == "Polygon":
        yield list(geom.exterior.coords)
    elif geom.geom_type == "MultiPolygon":
        for p in geom.geoms:
            yield list(p.exterior.coords)


def rings_from_pyshp(shape):
    parts = list(shape.parts) + [len(shape.points)]
    for i in range(len(parts) - 1):
        yield shape.points[parts[i]:parts[i + 1]]


def polygons_to_xy(list_of_rings):
    """Concat many polygon rings into one x,y arrays separated by None, for a single Plotly trace."""
    xs, ys = [], []
    for ring in list_of_rings:
        if len(ring) < 3:
            continue
        rx, ry = zip(*ring)
        xs.extend(rx)
        xs.append(None)
        ys.extend(ry)
        ys.append(None)
    return xs, ys


def bounds_of_rings(list_of_rings, pad_frac=0.04):
    all_x = [p[0] for ring in list_of_rings for p in ring]
    all_y = [p[1] for ring in list_of_rings for p in ring]
    if not all_x:
        return None
    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = min(all_y), max(all_y)
    px, py = (xmax - xmin) * pad_frac, (ymax - ymin) * pad_frac
    return xmin - px, xmax + px, ymin - py, ymax + py
