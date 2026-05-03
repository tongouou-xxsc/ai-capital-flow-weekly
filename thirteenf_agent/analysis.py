from __future__ import annotations

from collections import defaultdict

from .models import Holding, PositionChange


def compare_holdings(current: list[Holding], previous: list[Holding]) -> list[PositionChange]:
    current_by_key = {holding.key: holding for holding in current}
    previous_by_key = {holding.key: holding for holding in previous}
    changes: list[PositionChange] = []

    for key, holding in current_by_key.items():
        old = previous_by_key.get(key)
        if not old:
            changes.append(
                PositionChange(
                    kind="Added",
                    issuer=holding.issuer,
                    cusip=holding.cusip,
                    sector=holding.sector,
                    current_value_usd=holding.value_usd,
                    previous_value_usd=0,
                    current_shares=holding.shares,
                    previous_shares=0,
                )
            )
        elif holding.shares > old.shares:
            changes.append(change_from_pair("Increased", holding, old))
        elif holding.shares < old.shares:
            changes.append(change_from_pair("Reduced", holding, old))

    for key, old in previous_by_key.items():
        if key not in current_by_key:
            changes.append(
                PositionChange(
                    kind="Closed",
                    issuer=old.issuer,
                    cusip=old.cusip,
                    sector=old.sector,
                    current_value_usd=0,
                    previous_value_usd=old.value_usd,
                    current_shares=0,
                    previous_shares=old.shares,
                )
            )

    return sorted(changes, key=lambda change: abs(change.value_delta), reverse=True)


def change_from_pair(kind: str, current: Holding, previous: Holding) -> PositionChange:
    return PositionChange(
        kind=kind,
        issuer=current.issuer,
        cusip=current.cusip,
        sector=current.sector,
        current_value_usd=current.value_usd,
        previous_value_usd=previous.value_usd,
        current_shares=current.shares,
        previous_shares=previous.shares,
    )


def sector_totals(holdings: list[Holding]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for holding in holdings:
        totals[holding.sector] += holding.value_usd
    return dict(totals)


def sector_flow(changes: list[PositionChange]) -> tuple[str, str]:
    inflow: dict[str, int] = defaultdict(int)
    outflow: dict[str, int] = defaultdict(int)
    for change in changes:
        if change.kind in {"Added", "Increased"}:
            inflow[change.sector] += max(change.value_delta, change.current_value_usd)
        if change.kind in {"Reduced", "Closed"}:
            outflow[change.sector] += abs(min(change.value_delta, -change.previous_value_usd))
    from_sector = max(outflow.items(), key=lambda item: item[1], default=("Other", 0))[0]
    to_sector = max(inflow.items(), key=lambda item: item[1], default=("Other", 0))[0]
    return from_sector, to_sector


def key_bottleneck(changes: list[PositionChange]) -> str:
    inflow: dict[str, int] = defaultdict(int)
    for change in changes:
        if change.kind in {"Added", "Increased"}:
            inflow[change.sector] += max(change.value_delta, change.current_value_usd)
    priority = ["Power / Energy", "Data Center", "Networking", "AI Chips", "AI Cloud"]
    meaningful = {sector: value for sector, value in inflow.items() if value > 0}
    for sector in priority:
        if sector in meaningful:
            return sector
    return max(meaningful.items(), key=lambda item: item[1], default=("Other", 0))[0]
