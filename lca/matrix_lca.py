"""
Scipy-based LCA using premise-exported sparse matrices.
Used when premise databases exist but are in bw2data 4.x (incompatible with dashboard's bw2data 3.x).

Matrix files come from ndb.write_db_to_matrices() and are structured as:
  prospective/export/{model}/{pathway}/{year}/
      A_matrix.csv        — technosphere matrix coordinates
      A_matrix_index.csv  — activity labels (name, ref product, unit, location, index)
      B_matrix.csv        — biosphere matrix coordinates
      B_matrix_index.csv  — flow labels (name, compartment, subcompartment, unit, index)
"""

import json
from pathlib import Path
from csv import reader

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

MATRIX_BASE = Path(__file__).parents[1] / "prospective" / "export"
CF_FILE     = Path(__file__).parents[1] / "prospective" / "gwp100_cf.json"


def _matrix_dir(model: str, pathway: str, year: int) -> Path:
    return MATRIX_BASE / model / pathway / str(year)


def matrices_exist(model: str, pathway: str, year: int) -> bool:
    d = _matrix_dir(model, pathway, year)
    return all((d / f).exists() for f in ["A_matrix.csv", "A_matrix_index.csv",
                                           "B_matrix.csv", "B_matrix_index.csv"])


def _load_index(filepath: Path) -> dict:
    idx = {}
    with open(filepath, "r") as f:
        for row in reader(f, delimiter=";"):
            if len(row) >= 5:
                idx[tuple(row[:4])] = int(row[4])
    return idx


def _build_sparse(csv_path: Path, shape=None):
    coords = np.genfromtxt(csv_path, delimiter=";", skip_header=1)
    if coords.ndim == 1:
        coords = coords.reshape(1, -1)
    I = coords[:, 0].astype(int)
    J = coords[:, 1].astype(int)
    V = coords[:, 2]
    if shape is None:
        shape = (I.max() + 1, J.max() + 1)
    return sparse.csr_matrix((V, (I, J)), shape=shape)


def _load_cf(b_index: dict) -> np.ndarray:
    with open(CF_FILE) as f:
        cf_map = json.load(f)

    gwp = np.zeros(len(b_index))
    for (name, *_), idx in b_index.items():
        if name in cf_map:
            gwp[idx] = cf_map[name]
    return gwp


def lca_score_matrix(
    activity_name: str,
    model: str,
    pathway: str,
    year: int,
    scale_factor: float = 1.0,
) -> float:
    """
    Compute GWP100 (kg CO2-eq) for one functional unit of activity_name
    using premise-exported sparse matrices.
    """
    d = _matrix_dir(model, pathway, year)

    A_idx = _load_index(d / "A_matrix_index.csv")
    B_idx = _load_index(d / "B_matrix_index.csv")

    n = len(A_idx)
    m = len(B_idx)

    A_raw = np.genfromtxt(d / "A_matrix.csv", delimiter=";", skip_header=1)
    if A_raw.ndim == 1:
        A_raw = A_raw.reshape(1, -1)
    A = sparse.csr_matrix(
        (A_raw[:, 2], (A_raw[:, 1].astype(int), A_raw[:, 0].astype(int))),
        shape=(n, n),
    )

    B_raw = np.genfromtxt(d / "B_matrix.csv", delimiter=";", skip_header=1)
    if B_raw.ndim == 1:
        B_raw = B_raw.reshape(1, -1)
    B = sparse.csr_matrix(
        (B_raw[:, 2] * -1, (B_raw[:, 0].astype(int), B_raw[:, 1].astype(int))),
        shape=(n, m),
    )

    gwp = _load_cf(B_idx)

    # Find activity column
    A_idx_rev = {v: k for k, v in A_idx.items()}
    col = next(
        (idx for (name, *_), idx in A_idx.items()
         if activity_name.lower() in name.lower()),
        None,
    )
    if col is None:
        raise KeyError(f"Activity '{activity_name}' not found in A_matrix_index.")

    f = np.zeros(n)
    f[col] = 1.0
    s = spsolve(A, f)
    score = float((s @ B) @ gwp)
    return score * scale_factor
