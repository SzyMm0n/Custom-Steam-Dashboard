from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CFGNode:
    id: int
    label: str


@dataclass(frozen=True)
class CFGEdge:
    src: int
    dst: int
    label: str | None = None


@dataclass
class CFG:
    nodes: list[CFGNode]
    edges: list[CFGEdge]
    entry_id: int
    exit_id: int


def _node_label(stmt: ast.AST) -> str:
    lineno = getattr(stmt, "lineno", "?")
    kind = type(stmt).__name__

    extra = ""
    if isinstance(stmt, ast.If):
        extra = "if"
    elif isinstance(stmt, ast.For):
        extra = "for"
    elif isinstance(stmt, ast.While):
        extra = "while"
    elif isinstance(stmt, ast.Try):
        extra = "try"
    elif isinstance(stmt, ast.Raise):
        extra = "raise"
    elif isinstance(stmt, ast.Return):
        extra = "return"
    elif isinstance(stmt, ast.Expr):
        extra = "expr"
    elif isinstance(stmt, ast.Assign):
        extra = "assign"

    if extra:
        return f"L{lineno}: {kind} ({extra})"
    return f"L{lineno}: {kind}"


class _Builder:
    def __init__(self) -> None:
        self._next_id = 1
        self.nodes: list[CFGNode] = []
        self.edges: list[CFGEdge] = []

        self.entry_id = self._new_node("ENTRY")
        self.exit_id = self._new_node("EXIT")

    def _new_node(self, label: str) -> int:
        node_id = self._next_id
        self._next_id += 1
        self.nodes.append(CFGNode(node_id, label))
        return node_id

    def _edge(self, src: int, dst: int, label: str | None = None) -> None:
        self.edges.append(CFGEdge(src, dst, label))

    def build_block(self, stmts: Iterable[ast.stmt], prev: int, follow: int) -> int:
        """Build CFG for a sequence of statements.

        Returns the last node id in the linearized flow (may be follow).
        """
        last = prev
        for s in stmts:
            last = self.build_stmt(s, last, follow)
        return last

    def build_stmt(self, s: ast.stmt, prev: int, follow: int) -> int:
        # Control flow statements
        if isinstance(s, ast.If):
            cond = self._new_node(_node_label(s))
            self._edge(prev, cond)

            then_end = self.build_block(s.body, cond, follow)
            self._edge(cond, follow if not s.body else (then_end if then_end != cond else follow), "then")

            if s.orelse:
                else_end = self.build_block(s.orelse, cond, follow)
                self._edge(cond, follow if not s.orelse else (else_end if else_end != cond else follow), "else")
            else:
                self._edge(cond, follow, "else")

            return follow

        if isinstance(s, (ast.For, ast.While)):
            loop = self._new_node(_node_label(s))
            self._edge(prev, loop)

            body_end = self.build_block(s.body, loop, loop)
            # back edge
            self._edge(body_end if body_end != loop else loop, loop, "back")
            # loop exit
            self._edge(loop, follow, "exit")

            if s.orelse:
                self.build_block(s.orelse, loop, follow)

            return follow

        if isinstance(s, ast.Try):
            t = self._new_node(_node_label(s))
            self._edge(prev, t)

            # try body
            try_end = self.build_block(s.body, t, follow)
            self._edge(try_end if try_end != t else t, follow, "try_ok")

            # except handlers
            for h in s.handlers:
                h_node = self._new_node(f"L{getattr(h, 'lineno', '?')}: ExceptHandler")
                self._edge(t, h_node, "except")
                h_end = self.build_block(h.body, h_node, follow)
                self._edge(h_end if h_end != h_node else h_node, follow, "except_ok")

            # finally
            if s.finalbody:
                f_node = self._new_node(f"L{getattr(s, 'lineno', '?')}: finally")
                self._edge(t, f_node, "finally")
                f_end = self.build_block(s.finalbody, f_node, follow)
                self._edge(f_end if f_end != f_node else f_node, follow, "finally_ok")

            return follow

        if isinstance(s, (ast.Return, ast.Raise)):
            n = self._new_node(_node_label(s))
            self._edge(prev, n)
            self._edge(n, self.exit_id)
            return n

        # Default: linear statement
        n = self._new_node(_node_label(s))
        self._edge(prev, n)
        self._edge(n, follow)
        return n


def build_cfg_for_function(file_path: Path, function_qualname: str) -> CFG:
    """Build a best-effort CFG for a (possibly nested/class) function.

    function_qualname examples:
    - verify_jwt
    - verify_request_signature
    - GameDetailPanel._load_from_server (class method)

    This is intended as an illustrative visualization, not a full-program CFG.
    """
    mod = ast.parse(file_path.read_text(encoding="utf-8"))

    target_parts = function_qualname.split(".")

    def find_in(body: list[ast.stmt], parts: list[str]) -> ast.AST | None:
        if not parts:
            return None
        head, *tail = parts
        for node in body:
            if isinstance(node, ast.FunctionDef) and node.name == head and not tail:
                return node
            if isinstance(node, ast.AsyncFunctionDef) and node.name == head and not tail:
                return node
            if isinstance(node, ast.ClassDef) and node.name == head and tail:
                found = find_in(node.body, tail)
                if found is not None:
                    return found
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == head and tail:
                found = find_in(node.body, tail)
                if found is not None:
                    return found
        return None

    target = find_in(mod.body, target_parts)
    if target is None or not isinstance(target, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError(f"Function not found: {function_qualname} in {file_path}")

    b = _Builder()
    follow = b.exit_id
    b.build_block(target.body, b.entry_id, follow)

    return CFG(nodes=b.nodes, edges=b.edges, entry_id=b.entry_id, exit_id=b.exit_id)


def cfg_to_dot(cfg: CFG, title: str) -> str:
    lines: list[str] = []
    lines.append("digraph cfg {")
    lines.append('  rankdir=TB;')
    lines.append('  node [shape=box, fontname="Consolas"];')
    lines.append(f'  labelloc="t"; label="{title}";')

    for n in cfg.nodes:
        safe = n.label.replace('"', "'")
        lines.append(f'  n{n.id} [label="{safe}"];')

    for e in cfg.edges:
        if e.label:
            lines.append(f'  n{e.src} -> n{e.dst} [label="{e.label}"];')
        else:
            lines.append(f'  n{e.src} -> n{e.dst};')

    lines.append("}")
    return "\n".join(lines) + "\n"
