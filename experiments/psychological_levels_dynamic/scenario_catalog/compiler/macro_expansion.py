"""Deterministic macro expansion engine.

Consumes a GrammarProgram and produces an ExpansionResult. Structural
decomposition and row_budget allocation only: no scheduling, no timeline,
no geometry resolution, no price generation, no scenario specification.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import Enum
from typing import Any

from ..grammar.ast import GrammarParameter, GrammarProgram, PhraseType
from .diagnostics import CompilerDiagnostic, DiagnosticSeverity
from .expansion import AllocationPolicy, ExpandedInstruction, ExpansionResult, ExpansionRule
from .primitives import PrimitiveInstruction, PrimitiveType


ATOMIC_PASSTHROUGH: dict[PhraseType, PrimitiveType] = {
    PhraseType.HOLD: PrimitiveType.HOLD,
    PhraseType.RAMP: PrimitiveType.RAMP,
    PhraseType.OSCILLATE: PrimitiveType.OSCILLATE,
    PhraseType.APPROACH_ZONE: PrimitiveType.APPROACH,
    PhraseType.ENTER_ZONE: PrimitiveType.ENTER,
    PhraseType.PENETRATE: PrimitiveType.PENETRATE,
    PhraseType.WITHDRAW: PrimitiveType.WITHDRAW,
    PhraseType.HOLD_OUTSIDE: PrimitiveType.HOLD_OUTSIDE,
    PhraseType.RECOVERY_GAP: PrimitiveType.RECOVERY_GAP,
}

EXPANSION_RULES: dict[PhraseType, ExpansionRule] = {
    PhraseType.ACCEPTED_BREAK: ExpansionRule(
        macro_type=PhraseType.ACCEPTED_BREAK,
        primitive_sequence=(
            PrimitiveType.APPROACH,
            PrimitiveType.ENTER,
            PrimitiveType.PENETRATE,
            PrimitiveType.WITHDRAW,
            PrimitiveType.HOLD_OUTSIDE,
        ),
        allocation_rule_version="1",
    ),
    PhraseType.RECLAIM: ExpansionRule(
        macro_type=PhraseType.RECLAIM,
        primitive_sequence=(
            PrimitiveType.APPROACH,
            PrimitiveType.ENTER,
            PrimitiveType.PENETRATE,
            PrimitiveType.HOLD,
        ),
        allocation_rule_version="1",
    ),
    PhraseType.TRANSFER_TO_ZONE: ExpansionRule(
        macro_type=PhraseType.TRANSFER_TO_ZONE,
        primitive_sequence=(
            PrimitiveType.WITHDRAW,
            PrimitiveType.RAMP,
            PrimitiveType.APPROACH,
        ),
        allocation_rule_version="1",
    ),
    PhraseType.COMPRESS: ExpansionRule(
        macro_type=PhraseType.COMPRESS,
        primitive_sequence=(PrimitiveType.OSCILLATE,),
        allocation_rule_version="1",
    ),
    PhraseType.EXPAND: ExpansionRule(
        macro_type=PhraseType.EXPAND,
        primitive_sequence=(PrimitiveType.OSCILLATE,),
        allocation_rule_version="1",
    ),
}

_VARIABLE_ARITY_MACROS = frozenset({PhraseType.COMPRESS, PhraseType.EXPAND})

ALLOCATION_POLICY_V1 = AllocationPolicy(
    policy_name="EQUAL_DIVISION_REMAINDER_TO_FIRST",
    policy_version="1",
    description=(
        "Integer floor division of row_budget across primitives; the "
        "remainder is assigned one extra row each to the first N "
        "primitives, where N is the remainder."
    ),
)

ALLOCATION_POLICY_REGISTRY: dict[str, AllocationPolicy] = {
    ALLOCATION_POLICY_V1.policy_version: ALLOCATION_POLICY_V1,
}


def _fatal(
    code: str,
    phrase_index: int | None,
    message: str,
    parameter_name: str | None = None,
) -> CompilerDiagnostic:
    return CompilerDiagnostic(
        code=code,
        severity=DiagnosticSeverity.FATAL,
        message=message,
        phrase_index=phrase_index,
        parameter_name=parameter_name,
    )


def _find_parameter(params: tuple[GrammarParameter, ...], name: str) -> Any:
    for param in params:
        if param.name == name:
            return param.value
    return None


def _allocate(total_budget: int, primitive_count: int) -> tuple[int, ...] | None:
    if primitive_count <= 0 or primitive_count > total_budget:
        return None
    base, remainder = divmod(total_budget, primitive_count)
    return tuple(
        base + (1 if index < remainder else 0) for index in range(primitive_count)
    )


def _parameters(
    params: tuple[GrammarParameter, ...],
    *names: str,
    additions: tuple[GrammarParameter, ...] = (),
) -> tuple[GrammarParameter, ...]:
    selected = tuple(param for param in params if param.name in names)
    return tuple(sorted(selected + additions, key=lambda param: param.name))


def _expand_phrase(
    phrase: Any,
    phrase_index: int,
    start_index: int,
    diagnostics: list[CompilerDiagnostic],
) -> list[ExpandedInstruction] | None:
    if phrase.row_budget <= 0:
        diagnostics.append(
            _fatal("NEGATIVE_BUDGET", phrase_index, "phrase row_budget must be positive")
        )
        return None

    if phrase.phrase_type in ATOMIC_PASSTHROUGH:
        instruction = PrimitiveInstruction(
            instruction_index=start_index,
            source_phrase_index=phrase_index,
            primitive_type=ATOMIC_PASSTHROUGH[phrase.phrase_type],
            parameters=phrase.params,
            target_zone=phrase.target_zone,
            macro_origin=None,
        )
        return [ExpandedInstruction(instruction, phrase.row_budget)]

    rule = EXPANSION_RULES.get(phrase.phrase_type)
    if rule is None:
        diagnostics.append(
            _fatal(
                "MISSING_EXPANSION_RULE",
                phrase_index,
                f"no V1 expansion rule registered for {phrase.phrase_type.value}",
            )
        )
        return None
    if rule.macro_type != phrase.phrase_type:
        diagnostics.append(
            _fatal(
                "EXPANSION_RULE_VERSION_MISMATCH",
                phrase_index,
                "rule table entry does not declare the macro type it is filed under",
            )
        )
        return None

    policy = ALLOCATION_POLICY_REGISTRY.get(rule.allocation_rule_version)
    if policy is None:
        diagnostics.append(
            _fatal(
                "UNKNOWN_ALLOCATION_POLICY",
                phrase_index,
                f"allocation_rule_version {rule.allocation_rule_version!r} is not registered",
                parameter_name="allocation_rule_version",
            )
        )
        return None
    if policy.policy_version != rule.allocation_rule_version:
        diagnostics.append(
            _fatal(
                "ALLOCATION_POLICY_VERSION_MISMATCH",
                phrase_index,
                "registered policy_version does not match rule allocation_rule_version",
            )
        )
        return None

    schedule: tuple[Any, ...] | None = None
    if phrase.phrase_type in _VARIABLE_ARITY_MACROS:
        schedule = _find_parameter(phrase.params, "amplitude_schedule")
        if not isinstance(schedule, tuple) or len(schedule) == 0:
            diagnostics.append(
                _fatal(
                    "MISSING_REQUIRED_GRAMMAR_PARAMETER",
                    phrase_index,
                    "amplitude_schedule must be a non-empty tuple",
                    parameter_name="amplitude_schedule",
                )
            )
            return None
        primitive_types = tuple(rule.primitive_sequence[0] for _ in schedule)
    else:
        primitive_types = rule.primitive_sequence

    primitive_count = len(primitive_types)
    reserved_parameter_name: str | None = None
    if phrase.phrase_type == PhraseType.ACCEPTED_BREAK:
        reserved_parameter_name = "acceptance_rows"
    elif phrase.phrase_type == PhraseType.RECLAIM:
        reserved_parameter_name = "residence_rows"

    allocated_count = primitive_count
    reserved_rows: int | None = None
    if reserved_parameter_name is not None:
        reserved_rows = _find_parameter(phrase.params, reserved_parameter_name)
        if reserved_rows is None:
            diagnostics.append(
                _fatal(
                    "MISSING_REQUIRED_GRAMMAR_PARAMETER",
                    phrase_index,
                    f"{reserved_parameter_name} is required for {phrase.phrase_type.value}",
                    parameter_name=reserved_parameter_name,
                )
            )
            return None
        if type(reserved_rows) is not int or reserved_rows <= 0:
            diagnostics.append(
                _fatal(
                    "INVALID_RESERVED_BUDGET",
                    phrase_index,
                    "reserved row budget must be a positive integer",
                    parameter_name=reserved_parameter_name,
                )
            )
            return None
        allocated_count -= 1

    if reserved_rows is not None:
        allocation = _allocate(phrase.row_budget - reserved_rows, allocated_count)
        if allocation is not None:
            allocation += (reserved_rows,)
    else:
        allocation = _allocate(phrase.row_budget, allocated_count)
    if allocation is None:
        diagnostics.append(
            _fatal(
                "ALLOCATION_MISMATCH",
                phrase_index,
                f"row_budget {phrase.row_budget} cannot give at least one row "
                f"to each of {primitive_count} primitives",
            )
        )
        return None
    if sum(allocation) != phrase.row_budget:
        diagnostics.append(
            _fatal(
                "BUDGET_MISMATCH",
                phrase_index,
                "allocated row_budget total does not equal phrase row_budget",
            )
        )
        return None
    if any(value <= 0 for value in allocation):
        diagnostics.append(
            _fatal(
                "NEGATIVE_BUDGET",
                phrase_index,
                "allocation produced a non-positive row_budget",
            )
        )
        return None

    instructions: list[ExpandedInstruction] = []
    for offset, (primitive_type, row_budget) in enumerate(zip(primitive_types, allocation)):
        target_zone = phrase.target_zone
        if phrase.phrase_type == PhraseType.ACCEPTED_BREAK:
            names = {
                PrimitiveType.APPROACH: ("side", "clearance"),
                PrimitiveType.ENTER: ("side", "clearance"),
                PrimitiveType.PENETRATE: ("side", "clearance"),
                PrimitiveType.WITHDRAW: ("side", "clearance"),
                PrimitiveType.HOLD_OUTSIDE: ("side", "clearance", "acceptance_rows"),
            }[primitive_type]
            parameters = _parameters(phrase.params, *names)
        elif phrase.phrase_type == PhraseType.RECLAIM:
            names = {
                PrimitiveType.APPROACH: ("side", "depth"),
                PrimitiveType.ENTER: ("side", "depth"),
                PrimitiveType.PENETRATE: ("side", "depth"),
                PrimitiveType.HOLD: ("side", "depth", "residence_rows"),
            }[primitive_type]
            parameters = _parameters(phrase.params, *names)
        elif phrase.phrase_type == PhraseType.TRANSFER_TO_ZONE:
            parameters = _parameters(phrase.params, "source_zone", "travel_distance")
            if primitive_type == PrimitiveType.WITHDRAW:
                target_zone = _find_parameter(phrase.params, "source_zone")
        elif phrase.phrase_type in _VARIABLE_ARITY_MACROS:
            parameters = _parameters(
                phrase.params,
                "period_rows",
                additions=(GrammarParameter("amplitude", schedule[offset]),),
            )
        else:
            parameters = phrase.params
        instruction = PrimitiveInstruction(
            instruction_index=start_index + offset,
            source_phrase_index=phrase_index,
            primitive_type=primitive_type,
            parameters=parameters,
            target_zone=target_zone,
            macro_origin=phrase.phrase_type.value,
        )
        instructions.append(ExpandedInstruction(instruction, row_budget))
    return instructions


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": value.value}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Decimal):
        normalized = value.normalize()
        text = "0" if normalized == 0 else format(normalized, "f")
        return {"type": "decimal", "value": text}
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, GrammarParameter):
        return {"name": value.name, "value": _canonical(value.value)}
    if isinstance(value, PrimitiveInstruction):
        return {
            "instruction_index": value.instruction_index,
            "source_phrase_index": value.source_phrase_index,
            "primitive_type": _canonical(value.primitive_type),
            "parameters": _canonical(value.parameters),
            "target_zone": value.target_zone,
            "macro_origin": value.macro_origin,
        }
    if isinstance(value, ExpandedInstruction):
        return {
            "instruction": _canonical(value.instruction),
            "row_budget": value.row_budget,
        }
    if isinstance(value, CompilerDiagnostic):
        return {
            "code": value.code,
            "severity": _canonical(value.severity),
            "message": value.message,
            "phrase_index": value.phrase_index,
            "parameter_name": value.parameter_name,
        }
    raise TypeError(f"unsupported type for fingerprint canonicalization: {type(value).__name__}")


def _expansion_fingerprint(
    expanded_instructions: tuple[ExpandedInstruction, ...],
    grammar_fingerprint: str,
    compiler_version: str,
    diagnostics: tuple[CompilerDiagnostic, ...],
) -> str:
    payload = {
        "expanded_instructions": _canonical(expanded_instructions),
        "grammar_fingerprint": grammar_fingerprint,
        "compiler_version": compiler_version,
        "diagnostics": _canonical(diagnostics),
    }
    canonical_json = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return "sha256:" + hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def expand_program(program: GrammarProgram, compiler_version: str) -> ExpansionResult:
    if not isinstance(program, GrammarProgram):
        raise TypeError("program must be GrammarProgram")

    diagnostics: list[CompilerDiagnostic] = []
    expanded: list[ExpandedInstruction] = []
    next_index = 0

    for phrase_index, phrase in enumerate(program.phrases):
        outcome = _expand_phrase(phrase, phrase_index, next_index, diagnostics)
        if outcome is None:
            continue
        expanded.extend(outcome)
        next_index += len(outcome)

    indices = [item.instruction.instruction_index for item in expanded]
    if len(indices) != len(set(indices)):
        diagnostics.append(
            _fatal(
                "INSTRUCTION_INDEX_DUPLICATION",
                None,
                "duplicate instruction_index values in expanded output",
            )
        )

    has_fatal = any(item.severity == DiagnosticSeverity.FATAL for item in diagnostics)
    final_instructions: tuple[ExpandedInstruction, ...] = () if has_fatal else tuple(expanded)
    sorted_diagnostics = tuple(sorted(diagnostics, key=lambda item: item.deterministic_key))

    expansion_fingerprint = _expansion_fingerprint(
        final_instructions,
        program.program_fingerprint,
        compiler_version,
        sorted_diagnostics,
    )

    return ExpansionResult(
        success=not has_fatal,
        expanded_instructions=final_instructions,
        diagnostics=sorted_diagnostics,
        grammar_fingerprint=program.program_fingerprint,
        compiler_version=compiler_version,
        expansion_fingerprint=expansion_fingerprint,
    )
