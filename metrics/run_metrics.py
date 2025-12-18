from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from cfg_vis import build_cfg_for_function, cfg_to_dot


REPO_ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = REPO_ROOT / "metrics"
CFG_DIR = METRICS_DIR / "cfg"
BACKEND_DIR = REPO_ROOT / "server"
FRONTEND_DIR = REPO_ROOT / "app"


@dataclass(frozen=True)
class RunResult:
    stdout: str
    stderr: str
    returncode: int


def _run(cmd: list[str], cwd: Path) -> RunResult:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return RunResult(proc.stdout, proc.stderr, proc.returncode)


def _ensure_dirs() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)


def _python() -> str:
    return sys.executable


def _run_radon_json(args: list[str], out_path: Path) -> dict[str, Any]:
    cmd = [_python(), "-m", "radon", *args]
    res = _run(cmd, cwd=REPO_ROOT)
    if res.returncode != 0:
        raise RuntimeError(
            "Radon failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Exit code: {res.returncode}\n"
            f"STDERR:\n{res.stderr}\n"
        )
    out_path.write_text(res.stdout, encoding="utf-8")
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON from radon output: {out_path}") from exc


def _which(program: str) -> str | None:
    return shutil.which(program)


def _find_dot() -> str | None:
    dot = _which("dot")
    if dot:
        return dot

    # Common Graphviz locations on Windows
    candidates: list[Path] = []
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    local_appdata = os.environ.get("LOCALAPPDATA")

    if program_files:
        candidates.append(Path(program_files) / "Graphviz" / "bin" / "dot.exe")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Graphviz" / "bin" / "dot.exe")

    # winget package cache (Graphviz.Graphviz)
    if local_appdata:
        pkg_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if pkg_root.exists():
            for pkg in pkg_root.glob("Graphviz.Graphviz*"):
                try:
                    found = next(pkg.rglob("dot.exe"))
                    candidates.append(found)
                    break
                except StopIteration:
                    continue

    for c in candidates:
        if c.exists():
            return str(c)
    return None


def _render_dot_to_png(dot_path: Path, png_path: Path) -> bool:
    dot = _find_dot()
    if not dot:
        return False
    res = _run([dot, "-Tpng", str(dot_path), "-o", str(png_path)], cwd=REPO_ROOT)
    return res.returncode == 0


def _find_cloc() -> str | None:
    """Find cloc executable.

    Priority:
    1) PATH (standard)
    2) winget user package folder (common on Windows where PATH isn't updated)
    """
    on_path = _which("cloc")
    if on_path:
        return on_path

    local_appdata = Path((shutil.os.environ.get("LOCALAPPDATA") or "").strip())
    if not local_appdata:
        return None

    pkg_root = local_appdata / "Microsoft" / "WinGet" / "Packages"
    if not pkg_root.exists():
        return None

    # Example folder:
    # AlDanial.Cloc_Microsoft.Winget.Source_8wekyb3d8bbwe\cloc.exe
    for candidate in pkg_root.glob("AlDanial.Cloc_*\\cloc.exe"):
        if candidate.is_file():
            return str(candidate)

    return None


def _run_cloc_csv(out_csv: Path) -> tuple[bool, str | None]:
    cloc = _find_cloc()
    if not cloc:
        return False, None

    cmd = [
        cloc,
        "server",
        "app",
        "--csv",
        "--out",
        str(out_csv.relative_to(REPO_ROOT)),
    ]
    res = _run(cmd, cwd=REPO_ROOT)
    if res.returncode != 0:
        raise RuntimeError(
            "cloc failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Exit code: {res.returncode}\n"
            f"STDERR:\n{res.stderr}\n"
        )
    return True, cloc


def _run_cloc_lists(*, counted_path: Path, ignored_path: Path) -> bool:
    cloc = _find_cloc()
    if not cloc:
        return False

    cmd = [
        cloc,
        "server",
        "app",
        f"--counted={counted_path.relative_to(REPO_ROOT)}",
        f"--ignored={ignored_path.relative_to(REPO_ROOT)}",
        "--quiet",
    ]
    res = _run(cmd, cwd=REPO_ROOT)
    return res.returncode == 0 and counted_path.exists()


def _run_cloc_json(targets: list[Path]) -> dict[str, Any] | None:
    cloc = _find_cloc()
    if not cloc:
        return None

    rel_targets: list[str] = []
    for t in targets:
        try:
            rel_targets.append(str(t.relative_to(REPO_ROOT)))
        except ValueError:
            rel_targets.append(str(t))

    cmd = [cloc, *rel_targets, "--json"]
    res = _run(cmd, cwd=REPO_ROOT)
    if res.returncode != 0:
        raise RuntimeError(
            "cloc failed (JSON run).\n"
            f"Command: {' '.join(cmd)}\n"
            f"Exit code: {res.returncode}\n"
            f"STDERR:\n{res.stderr}\n"
        )

    # cloc sometimes prints progress to stderr; json is in stdout.
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _path_kind(file_path: str) -> str:
    p = Path(file_path.replace("\\", "/"))
    if "server/" in p.as_posix():
        return "backend"
    if "app/" in p.as_posix():
        return "frontend"
    return "other"


def _iter_cc_units(cc_json: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield flattened CC units: functions, methods, and classes if present."""
    for file_path, blocks in cc_json.items():
        if not isinstance(blocks, list):
            continue

        has_method_blocks = any(
            isinstance(b, dict) and str(b.get("type") or "").lower() == "method" for b in blocks
        )

        # Build a best-effort map of method identity -> qualified name from class blocks.
        qual_map: dict[tuple[Any, Any, Any], str] = {}
        for b in blocks:
            if not isinstance(b, dict):
                continue
            if str(b.get("type") or "").lower() != "class":
                continue
            cls_name = b.get("name")
            methods = b.get("methods")
            if not cls_name or not isinstance(methods, list):
                continue
            for m in methods:
                if not isinstance(m, dict):
                    continue
                key = (m.get("name"), m.get("lineno"), m.get("endline"))
                if key[0]:
                    qual_map[key] = f"{cls_name}.{key[0]}"

        for block in blocks:
            if not isinstance(block, dict):
                continue
            unit = dict(block)
            unit["__file"] = file_path

            if str(unit.get("type") or "").lower() == "method":
                key = (unit.get("name"), unit.get("lineno"), unit.get("endline"))
                qualified = qual_map.get(key)
                if qualified:
                    unit["qualified_name"] = qualified
            yield unit

            # Some radon versions embed methods under class blocks but do NOT emit standalone method blocks.
            # Only emit embedded methods when standalone method blocks are absent (avoids double counting).
            if not has_method_blocks and str(block.get("type") or "").lower() == "class":
                methods = block.get("methods")
                if isinstance(methods, list):
                    for m in methods:
                        if isinstance(m, dict):
                            unit_m = dict(m)
                            unit_m.setdefault("type", "method")
                            unit_m["__file"] = file_path
                            cls_name = block.get("name")
                            if cls_name and unit_m.get("name"):
                                unit_m["qualified_name"] = f"{cls_name}.{unit_m['name']}"
                            yield unit_m


def _dedupe_units(units: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicates that can appear depending on radon JSON shape."""
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for u in units:
        key = (
            u.get("__file"),
            str(u.get("type") or "").lower(),
            u.get("name"),
            u.get("qualified_name"),
            u.get("lineno"),
            u.get("endline"),
            u.get("complexity"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    return out


def _cc_name(unit: dict[str, Any]) -> str:
    return str(unit.get("qualified_name") or unit.get("name") or "<unknown>")


def _cc_rank(unit: dict[str, Any]) -> str:
    rank = unit.get("rank")
    if isinstance(rank, str) and rank:
        return rank

    # Some radon json variants store it as "letter".
    letter = unit.get("letter")
    if isinstance(letter, str) and letter:
        return letter

    return "?"


def _cc_complexity(unit: dict[str, Any]) -> int | None:
    c = unit.get("complexity")
    if isinstance(c, int):
        return c
    if isinstance(c, float):
        return int(c)
    if isinstance(c, str) and c.isdigit():
        return int(c)
    return None


def _is_function_like(unit: dict[str, Any]) -> bool:
    t = str(unit.get("type") or "").lower()
    return t in {"function", "method"}


def _is_class(unit: dict[str, Any]) -> bool:
    t = str(unit.get("type") or "").lower()
    return t == "class"


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _format_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _cloc_totals(cloc_json: dict[str, Any] | None) -> dict[str, int] | None:
    if not cloc_json:
        return None

    summary = cloc_json.get("SUM")
    if not isinstance(summary, dict):
        return None

    def _int(key: str) -> int:
        v = summary.get(key)
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    return {
        "files": _int("nFiles"),
        "blank": _int("blank"),
        "comment": _int("comment"),
        "code": _int("code"),
    }


def _collect_python_files(roots: list[Path]) -> set[str]:
    out: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            parts = {part.lower() for part in p.parts}
            if "__pycache__" in parts:
                continue
            try:
                rel = p.relative_to(REPO_ROOT)
            except ValueError:
                rel = p
            out.add(rel.as_posix())
    return out


def _radon_files_relative(radon_json: dict[str, Any]) -> set[str]:
    files: set[str] = set()
    for k in radon_json.keys():
        try:
            rel = Path(str(k)).resolve().relative_to(REPO_ROOT)
            files.add(rel.as_posix())
        except Exception:
            # Best-effort normalization
            files.add(str(k).replace("\\", "/"))
    return files


def _generate_report(
    *,
    cloc_available: bool,
    cloc_backend: dict[str, int] | None,
    cloc_frontend: dict[str, int] | None,
    cloc_total: dict[str, int] | None,
    cloc_loc_coverage: tuple[int, int, int] | None,
    cc_json: dict[str, Any],
    mi_json: dict[str, Any],
    raw_json: dict[str, Any],
    cc_missing_files: list[str],
    cfg_outputs: list[tuple[str, str, str | None]],
) -> str:
    # Coverage (files analyzed)
    expected_py_files = _collect_python_files([BACKEND_DIR, FRONTEND_DIR])
    cc_files = _radon_files_relative(cc_json)
    mi_files = _radon_files_relative(mi_json)
    raw_files = _radon_files_relative(raw_json)

    def _coverage_line(label: str, files: set[str]) -> str:
        total = len(expected_py_files)
        used_set = {f for f in files if f in expected_py_files}
        used = len(used_set)
        if total == 0:
            return f"- {label}: n/a (brak wykrytych plików .py w server/app)"
        if used == total:
            return f"- {label}: przeanalizowano wszystkie pliki Python ({used}/{total})"
        missing = total - used
        return f"- {label}: przeanalizowano podzbiór plików Python ({used}/{total}); brakujące: {missing} (nie wypisujemy)"

    # CC analysis
    cc_units = _dedupe_units(u for u in _iter_cc_units(cc_json) if _is_function_like(u))

    cc_backend = [u for u in cc_units if _path_kind(str(u.get("__file"))) == "backend"]
    cc_frontend = [u for u in cc_units if _path_kind(str(u.get("__file"))) == "frontend"]

    backend_cc_values = [float(_cc_complexity(u)) for u in cc_backend if _cc_complexity(u) is not None]
    frontend_cc_values = [float(_cc_complexity(u)) for u in cc_frontend if _cc_complexity(u) is not None]

    avg_cc_backend = _mean(backend_cc_values)
    avg_cc_frontend = _mean(frontend_cc_values)

    top_complex = sorted(
        [u for u in cc_units if _cc_complexity(u) is not None],
        key=lambda u: (_cc_complexity(u) or 0),
        reverse=True,
    )[:5]

    has_high_ranks = [u for u in cc_units if _cc_rank(u) in {"D", "E", "F"}]

    # MI analysis
    mi_entries: list[tuple[str, float, str]] = []
    for file_path, mi_data in mi_json.items():
        if not isinstance(mi_data, dict):
            continue
        mi = _safe_float(mi_data.get("mi"))
        rank = mi_data.get("rank")
        if mi is None or not isinstance(rank, str):
            continue
        mi_entries.append((file_path, mi, rank))

    mi_backend = [mi for (p, mi, _) in mi_entries if _path_kind(p) == "backend"]
    mi_frontend = [mi for (p, mi, _) in mi_entries if _path_kind(p) == "frontend"]

    avg_mi_backend = _mean(mi_backend)
    avg_mi_frontend = _mean(mi_frontend)

    lowest_mi = min(mi_entries, key=lambda t: t[1]) if mi_entries else None

    # OO-ish counts (from CC JSON)
    class_units = _dedupe_units(u for u in _iter_cc_units(cc_json) if _is_class(u))
    top_level_functions = _dedupe_units(
        u for u in _iter_cc_units(cc_json) if str(u.get("type") or "").lower() == "function"
    )

    # Methods count best-effort: either explicit method entries or methods lists.
    method_units = _dedupe_units(
        u for u in _iter_cc_units(cc_json) if str(u.get("type") or "").lower() == "method"
    )
    method_count = len(method_units)
    # If methods are embedded only, they were yielded with type=method above.

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _loc_block(title: str, totals: dict[str, int] | None) -> str:
        if not totals:
            return f"- {title}: n/a"
        return (
            f"- {title}: code={totals['code']}, comment={totals['comment']}, "
            f"blank={totals['blank']}, files={totals['files']}"
        )

    report_lines: list[str] = []
    report_lines.append("# METRICS REPORT — Custom-Steam-Dashboard")
    report_lines.append("")
    report_lines.append(f"Generated: {now}")
    report_lines.append("")

    report_lines.append("## Zakres analizy (pokrycie plików)")
    report_lines.append("- Katalogi: `server/` (backend), `app/` (frontend)")
    report_lines.append(f"- Wykryte pliki Python (*.py) w tych katalogach: {len(expected_py_files)}")
    report_lines.append(_coverage_line("Radon CC (złożoność)", cc_files))
    report_lines.append(_coverage_line("Radon MI (maintainability)", mi_files))
    report_lines.append(_coverage_line("Radon RAW (surowe metryki)", raw_files))
    if cc_missing_files:
        report_lines.append(
            "- Wyjaśnienie CC: `radon cc` raportuje tylko pliki, w których wykryje funkcje/metody/klasy. "
            "Pliki typu `__init__.py` bez definicji zwykle nie pojawiają się w JSON, mimo że były przetworzone." 
        )
        report_lines.append(
            f"- Lista plików nieobecnych w kluczach `radon_cc.json` została zapisana do: `metrics/radon_cc_missing_files.txt` (liczba: {len(cc_missing_files)})"
        )
    else:
        report_lines.append("- Uwaga: jeśli CC jest podzbiorem, typowe przyczyny to brak definicji w module albo błędy parsowania.")
    report_lines.append("")

    report_lines.append("## Narzędzia")
    report_lines.append("- `cloc` — LOC (kod/komentarze/puste linie)")
    report_lines.append("- `radon` — złożoność cyklomatyczna (CC), Maintainability Index (MI), metryki surowe/strukturalne")
    report_lines.append("")

    report_lines.append("## Linie kodu (LOC)")
    if cloc_available:
        report_lines.append(_loc_block("Cała aplikacja (server + app)", cloc_total))
        report_lines.append(_loc_block("Backend (server)", cloc_backend))
        report_lines.append(_loc_block("Frontend (app)", cloc_frontend))
        if cloc_loc_coverage:
            total_py, counted_py, missing_py = cloc_loc_coverage
            if total_py and missing_py:
                report_lines.append(
                    f"- Pokrycie LOC: `cloc` policzył {counted_py}/{total_py} plików `*.py`; pominięte: {missing_py} (najczęściej puste `__init__.py`)."
                )
                report_lines.append(
                    "- Listy pomocnicze: `metrics/cloc_counted.txt` (policzone) oraz `metrics/cloc_ignored.txt` (zignorowane + powód)."
                )
        report_lines.append("- Komentarz: interpretuj powyższe jako wielkość projektu (mały/średni) w kontekście Semgrepa.")
    else:
        report_lines.append("- `cloc` nie jest dostępny w PATH, więc LOC nie zostało policzone.")
        report_lines.append("- Zainstaluj `cloc` (Windows) i uruchom ponownie skrypt: `python metrics/run_metrics.py`. Szczegóły w `metrics/README.md`.")
    report_lines.append("")

    report_lines.append("## Złożoność cyklomatyczna (CC)")
    report_lines.append(f"- Średnia CC backend: {_format_float(avg_cc_backend)}")
    report_lines.append(f"- Średnia CC frontend: {_format_float(avg_cc_frontend)}")
    report_lines.append("- 3–5 najbardziej złożonych jednostek:")
    for u in top_complex:
        report_lines.append(
            f"  - {u.get('__file')}: {_cc_name(u)} | CC={_cc_complexity(u)} | rank={_cc_rank(u)}"
        )
    report_lines.append(
        "- Funkcje o rank D/E/F: "
        + ("TAK" if any(_cc_rank(u) in {"D", "E", "F"} for u in has_high_ranks) else "NIE")
    )
    report_lines.append("")

    report_lines.append("## Maintainability Index (MI)")
    report_lines.append(f"- Średni MI backend: {_format_float(avg_mi_backend)}")
    report_lines.append(f"- Średni MI frontend: {_format_float(avg_mi_frontend)}")
    if lowest_mi:
        report_lines.append(f"- Najniższy MI: {lowest_mi[0]} | MI={_format_float(lowest_mi[1])} | rank={lowest_mi[2]}")
    else:
        report_lines.append("- Najniższy MI: n/a")
    report_lines.append("- Interpretacja: >85 bardzo dobra, 65–85 poprawna, <65 trudna w utrzymaniu.")
    report_lines.append("")

    report_lines.append("## Metryki obiektowe (strukturalne)")
    report_lines.append(f"- Liczba klas: {len(class_units)}")
    report_lines.append(f"- Liczba funkcji (top-level): {len(top_level_functions)}")
    report_lines.append(f"- Liczba metod: {method_count}")
    report_lines.append("- Komentarz: liczby są wyliczane best-effort z danych `radon cc`, więc dotyczą tego samego zakresu plików co sekcja CC.")
    report_lines.append("")

    report_lines.append("## CFG – interpretacja")
    report_lines.append("- Nie generujemy pełnych grafów CFG dla całej aplikacji (Python dynamiczny, słaba skalowalność narzędzi).")
    report_lines.append("- CC (`radon cc`) jest liczona na podstawie CFG, więc traktujemy ją jako pośrednią metrykę CFG.")
    if cfg_outputs:
        report_lines.append("- Wygenerowane przykładowe wizualizacje CFG (2 funkcje z `server/security.py`):")
        for func, dot_path, png_path in cfg_outputs:
            if png_path:
                report_lines.append(f"  - {func}: DOT=`{dot_path}`, PNG=`{png_path}`")
            else:
                report_lines.append(f"  - {func}: DOT=`{dot_path}` (PNG: brak — zainstaluj Graphviz, polecenie `dot`) ")
    report_lines.append("")

    report_lines.append("## Wnioski końcowe")
    report_lines.append("- Uzupełnij krótką interpretację w kontekście wyników Semgrepa (czy metryki wspierają niską liczbę findings).")

    return "\n".join(report_lines) + "\n"


def main() -> int:
    _ensure_dirs()
    CFG_DIR.mkdir(parents=True, exist_ok=True)

    out_cc = METRICS_DIR / "radon_cc.json"
    out_mi = METRICS_DIR / "radon_mi.json"
    out_raw = METRICS_DIR / "radon_raw.json"
    out_cloc_csv = METRICS_DIR / "cloc_metrics.csv"
    out_cloc_counted = METRICS_DIR / "cloc_counted.txt"
    out_cloc_ignored = METRICS_DIR / "cloc_ignored.txt"
    out_report = METRICS_DIR / "METRICS_REPORT.md"
    out_cc_missing = METRICS_DIR / "radon_cc_missing_files.txt"

    print("[metrics] Running radon (cc, mi, raw)...")
    cc_json = _run_radon_json(["cc", str(BACKEND_DIR), str(FRONTEND_DIR), "-a", "-j"], out_cc)
    mi_json = _run_radon_json(["mi", str(BACKEND_DIR), str(FRONTEND_DIR), "-j"], out_mi)
    raw_json = _run_radon_json(["raw", str(BACKEND_DIR), str(FRONTEND_DIR), "-j"], out_raw)

    print("[metrics] Running cloc (optional)...")
    cloc_available, _ = _run_cloc_csv(out_cloc_csv)

    cloc_loc_coverage: tuple[int, int, int] | None = None
    if cloc_available:
        _run_cloc_lists(counted_path=out_cloc_counted, ignored_path=out_cloc_ignored)

    # For report: compute totals for backend/frontend/total using cloc JSON runs (if available)
    cloc_total = _cloc_totals(_run_cloc_json([BACKEND_DIR, FRONTEND_DIR])) if cloc_available else None
    cloc_backend = _cloc_totals(_run_cloc_json([BACKEND_DIR])) if cloc_available else None
    cloc_frontend = _cloc_totals(_run_cloc_json([FRONTEND_DIR])) if cloc_available else None

    # Determine which *.py files are missing from radon cc keys (typically __init__.py with no defs)
    expected_py_files = sorted(_collect_python_files([BACKEND_DIR, FRONTEND_DIR]))
    cc_files = sorted(_radon_files_relative(cc_json))
    cc_missing = sorted([p for p in expected_py_files if p not in set(cc_files)])
    out_cc_missing.write_text("\n".join(cc_missing) + ("\n" if cc_missing else ""), encoding="utf-8")

    # LOC coverage: compare *.py discovered vs cloc-counted files (helps explain file count differences)
    if cloc_available and out_cloc_counted.exists():
        counted = [ln.strip() for ln in out_cloc_counted.read_text(encoding="utf-8").splitlines() if ln.strip()]
        counted_set = {p.replace("\\", "/") for p in counted}
        expected_set = set(expected_py_files)
        missing_for_loc = sorted(expected_set - counted_set)
        cloc_loc_coverage = (len(expected_set), len(expected_set) - len(missing_for_loc), len(missing_for_loc))

    # CFG visualizations (illustrative): pick two representative functions from server/security.py
    cfg_outputs: list[tuple[str, str, str | None]] = []
    security_py = BACKEND_DIR / "security.py"
    for func in ["verify_request_signature", "verify_jwt"]:
        try:
            cfg = build_cfg_for_function(security_py, func)
            dot_text = cfg_to_dot(cfg, title=f"CFG: server/security.py::{func}")
            dot_path = (CFG_DIR / f"security__{func}.dot")
            dot_path.write_text(dot_text, encoding="utf-8")
            png_path = (CFG_DIR / f"security__{func}.png")
            png_ok = _render_dot_to_png(dot_path, png_path)
            cfg_outputs.append(
                (func, f"metrics/cfg/{dot_path.name}", f"metrics/cfg/{png_path.name}" if png_ok else None)
            )
        except Exception as e:
            print(f"[metrics] NOTE: CFG generation failed for {func}: {e}")

    print("[metrics] Generating METRICS_REPORT.md...")
    report = _generate_report(
        cloc_available=cloc_available,
        cloc_backend=cloc_backend,
        cloc_frontend=cloc_frontend,
        cloc_total=cloc_total,
        cloc_loc_coverage=cloc_loc_coverage,
        cc_json=cc_json,
        mi_json=mi_json,
        raw_json=raw_json,
        cc_missing_files=cc_missing,
        cfg_outputs=cfg_outputs,
    )
    out_report.write_text(report, encoding="utf-8")

    print("[metrics] Done.")
    print(f"[metrics] Outputs: {METRICS_DIR}")

    if not cloc_available:
        print("[metrics] NOTE: cloc not found in PATH; LOC section will be n/a.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
