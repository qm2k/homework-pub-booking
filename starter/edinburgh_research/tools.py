"""Ex5 tools. Four tools the agent uses to research an Edinburgh booking.

Each tool:
  1. Reads its fixture from sample_data/ (DO NOT modify the fixtures).
  2. Logs its arguments and output into _TOOL_CALL_LOG (see integrity.py).
  3. Returns a ToolResult with success=True/False, output=dict, summary=str.

The grader checks for:
  * Correct parallel_safe flags (reads True, generate_flyer False).
  * Every tool's results appear in _TOOL_CALL_LOG.
  * Tools fail gracefully on missing fixtures or bad inputs (ToolError,
    not RuntimeError).
"""

from __future__ import annotations

import html
import json
import math
import string
from pathlib import Path

import more_itertools

from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolRegistry, ToolResult, _RegisteredTool
from sovereign_agent.errors import ToolError

from .integrity import record_tool_call

_SAMPLE_DATA = Path(__file__).parent / "sample_data"
_VENUES_FILE = _SAMPLE_DATA / "venues.json"
_WEATHER_FILE = _SAMPLE_DATA / "weather.json"
_CATERING_FILE = _SAMPLE_DATA / "catering.json"
_FLYER_TEMPLATE = Path(__file__).parent / "flyer_template.html"
_ERR_MISSING = "SA_TOOL_DEPENDENCY_MISSING"
_ERR_EXECUTION_FAILED = "SA_TOOL_EXECUTION_FAILED"
_ERR_INVALID_INPUT = "SA_TOOL_INVALID_INPUT"

# ---------------------------------------------------------------------------
# venue_search
# ---------------------------------------------------------------------------
def _venue_search_filter(*, venue: dict, near_folded: str, party_size: int, budget_max_gbp: int) -> bool:
    """Evaluate if a venue meets the search criteria.
    
    Checks if the venue is open, located in the specified area (case-insensitive),
    has enough seats, and fits within the given maximum budget.
    """
    if not venue["open_now"]:
        return False
    if near_folded not in venue["area"].casefold():
        return False
    if venue["seats_available_evening"] < party_size:
        return False
    if venue["hire_fee_gbp"] + venue["min_spend_gbp"] > budget_max_gbp:
        return False
    return True


def venue_search(near: str, party_size: int, budget_max_gbp: int = 1000) -> ToolResult:
    """Search for Edinburgh venues near <near> that can seat the party.

    Reads sample_data/venues.json. Filters by:
      * open_now == True
      * area contains <near> (case-insensitive substring match)
      * seats_available_evening >= party_size
      * hire_fee_gbp + min_spend_gbp <= budget_max_gbp

    Returns a ToolResult with:
      output: {"near": ..., "party_size": ..., "results": [<venue dicts>], "count": int}
      summary: "venue_search(near='<near>', party_size=<party_size>, budget_max_gbp=<budget_max_gbp>): <count> result(s)"

    MUST call record_tool_call(...) before returning so the integrity
    check can see what data was produced.
    """
    try:
        with open(_VENUES_FILE, "r") as file_handle:
            venues = json.load(file_handle)

        # Pre-fold the search string for efficient case-insensitive comparison in the loop
        near_folded = near.casefold()
        
        results = [
            venue for venue in venues 
            if _venue_search_filter(
                venue=venue, 
                near_folded=near_folded, 
                party_size=party_size, 
                budget_max_gbp=budget_max_gbp
            )
        ]
        
        output = dict(
            near=near,
            party_size=party_size,
            results=results,
            count=len(results)
        )
        
        record_tool_call(
            tool_name="venue_search",
            arguments=dict(near=near, party_size=party_size, budget_max_gbp=budget_max_gbp),
            output=output
        )
        
        return ToolResult(
            success=True,
            output=output,
            summary=f"venue_search(near={near!r}, party_size={party_size}, budget_max_gbp={budget_max_gbp}): {len(results)} result(s)"
        )
    except FileNotFoundError as exception:
        raise ToolError(_ERR_MISSING, message=str(exception)) from exception
    except Exception as exception:
        raise ToolError(_ERR_EXECUTION_FAILED, message=str(exception)) from exception


# ---------------------------------------------------------------------------
# get_weather
# ---------------------------------------------------------------------------
def _get_weather_impl(*, city: str, date: str) -> ToolResult:
    """Implement weather lookup logic with early error returns."""
    with open(_WEATHER_FILE, "r") as file_handle:
        weather_data = json.load(file_handle)
        
    city_folded = city.casefold()
    
    if city_folded not in weather_data:
        return ToolResult(
            success=False,
            output=dict(error="City not found", city=city),
            summary=f"get_weather(city={city!r}, date={date!r}): City not found",
            error=ToolError(_ERR_INVALID_INPUT, message="City not found")
        )
        
    city_weather = weather_data[city_folded]
    
    if date not in city_weather:
        return ToolResult(
            success=False,
            output=dict(error="Date not found", city=city, date=date),
            summary=f"get_weather(city={city!r}, date={date!r}): Date not found",
            error=ToolError(_ERR_INVALID_INPUT, message="Date not found")
        )
        
    day_weather = city_weather[date]
    
    output = dict(
        city=city,
        date=date,
        **day_weather
    )
    
    condition = day_weather["condition"]
    temperature_c = day_weather["temperature_c"]
    
    return ToolResult(
        success=True,
        output=output,
        summary=f"get_weather(city={city!r}, date={date!r}): {condition}, {temperature_c}C"
    )

def get_weather(city: str, date: str) -> ToolResult:
    """Look up the scripted weather for <city> on <date> (YYYY-MM-DD).

    Reads sample_data/weather.json. Returns:
      output: {"city": str, "date": str, "condition": str, "temperature_c": int, ...}
      summary: "get_weather(city='<city>', date='<date>'): <condition>, <temp>C"

    If the city or date is not in the fixture, return success=False with
    a clear ToolError (SA_TOOL_INVALID_INPUT). Do NOT raise.

    MUST call record_tool_call(...) before returning.
    """
    try:
        result = _get_weather_impl(city=city, date=date)
        
        record_tool_call(
            tool_name="get_weather",
            arguments=dict(city=city, date=date),
            output=result.output
        )
        
        return result
    except FileNotFoundError as exception:
        raise ToolError(_ERR_MISSING, message=str(exception)) from exception
    except Exception as exception:
        raise ToolError(_ERR_EXECUTION_FAILED, message=str(exception)) from exception


# ---------------------------------------------------------------------------
# calculate_cost
# ---------------------------------------------------------------------------
def _get_deposit_policy_key(*, total: float) -> str:
    """Map the total cost to the corresponding deposit policy tier."""
    if total < 300:
        return "under_gbp_300"
    if total <= 1000:
        return "gbp_300_to_1000"
    return "over_gbp_1000"


def _get_deposit_factor(*, policy_value: str) -> float:
    """Convert a deposit policy string value to a numeric multiplier."""
    if policy_value == "deposit_20_percent":
        return 0.20
    if policy_value == "deposit_30_percent":
        return 0.30
    if policy_value == "no_deposit_required":
        return 0.0
    raise ValueError(f"Unknown deposit policy value: {policy_value}")


def _calculate_deposit_required(*, total: float, deposit_policy: dict) -> float:
    """Calculate the required deposit based on total cost and policy rules."""
    policy_key = _get_deposit_policy_key(total=total)
    policy_value = deposit_policy[policy_key]
    factor = _get_deposit_factor(policy_value=policy_value)
    return total * factor


def _calculate_cost_impl(
    *,
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str
) -> ToolResult:
    """Implement cost calculation logic.
    
    Raises ValueError if venue_id is not found, KeyError if catering_tier
    is invalid. These are caught by the wrapper and converted to SA_TOOL_INVALID_INPUT.
    """
    with open(_CATERING_FILE, "r") as file_handle:
        catering_data = json.load(file_handle)

    with open(_VENUES_FILE, "r") as file_handle:
        venues_data = json.load(file_handle)

    # Use more_itertools.one to ensure exactly one venue matches; raises ValueError otherwise
    venue = more_itertools.one(v for v in venues_data if v["id"] == venue_id)

    base_rates = catering_data["base_rates_gbp_per_head"]
    # Raises KeyError if catering_tier is not valid
    base_per_head = base_rates[catering_tier]
        
    # Assume 1.0 multiplier if venue not explicitly listed in modifiers
    venue_mult = catering_data["venue_modifiers"].get(venue_id, 1.0)
    
    subtotal = base_per_head * venue_mult * party_size * max(1, duration_hours)
    service = subtotal * catering_data["service_charge_percent"] / 100
    
    hire_fee = venue["hire_fee_gbp"]
    min_spend = venue["min_spend_gbp"]
    
    total = subtotal + service + hire_fee + min_spend
    
    deposit_policy = catering_data["deposit_policy"]
    deposit_required = _calculate_deposit_required(
        total=total, 
        deposit_policy=deposit_policy
    )

    # Use math.ceil to round up unrounded values at the very end
    total_int = math.ceil(total)
    subtotal_int = math.ceil(subtotal)
    service_int = math.ceil(service)
    deposit_required_int = math.ceil(deposit_required)

    output = dict(
        venue_id=venue_id,
        party_size=party_size,
        duration_hours=duration_hours,
        catering_tier=catering_tier,
        subtotal_gbp=subtotal_int,
        service_gbp=service_int,
        total_gbp=total_int,
        deposit_required_gbp=deposit_required_int,
    )
    
    return ToolResult(
        success=True,
        output=output,
        summary=f"calculate_cost(venue_id={venue_id!r}, party_size={party_size}, duration_hours={duration_hours}, catering_tier={catering_tier!r}): total £{total_int}, deposit £{deposit_required_int}"
    )


def calculate_cost(
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str = "bar_snacks",
) -> ToolResult:
    """Compute the total cost for a booking.

    Formula:
      base_per_head = base_rates_gbp_per_head[catering_tier]
      venue_mult    = venue_modifiers[venue_id]
      subtotal      = base_per_head * venue_mult * party_size * max(1, duration_hours)
      service       = subtotal * service_charge_percent / 100
      total         = subtotal + service + <venue's hire_fee_gbp + min_spend_gbp>
      deposit_rule  = per deposit_policy thresholds

    Returns:
      output: {
        "venue_id": str,
        "party_size": int,
        "duration_hours": int,
        "catering_tier": str,
        "subtotal_gbp": int,
        "service_gbp": int,
        "total_gbp": int,
        "deposit_required_gbp": int,
      }
      summary: "calculate_cost(venue_id='<venue>', party_size=<party_size>, duration_hours=<duration_hours>, catering_tier='<tier>'): total £<N>, deposit £<M>"

    MUST call record_tool_call(...) before returning.
    """
    try:
        result = _calculate_cost_impl(
            venue_id=venue_id,
            party_size=party_size,
            duration_hours=duration_hours,
            catering_tier=catering_tier
        )
        
        record_tool_call(
            tool_name="calculate_cost",
            arguments=dict(
                venue_id=venue_id,
                party_size=party_size,
                duration_hours=duration_hours,
                catering_tier=catering_tier
            ),
            output=result.output
        )
        
        return result
    except (ValueError, KeyError) as exception:
        # Invalid venue_id or catering_tier mapped to specific invalid input error
        raise ToolError(_ERR_INVALID_INPUT, message=str(exception)) from exception
    except FileNotFoundError as exception:
        raise ToolError(_ERR_MISSING, message=str(exception)) from exception
    except Exception as exception:
        raise ToolError(_ERR_EXECUTION_FAILED, message=str(exception)) from exception


# ---------------------------------------------------------------------------
# generate_flyer
# ---------------------------------------------------------------------------
def generate_flyer(session: Session, event_details: dict) -> ToolResult:
    """Produce an HTML flyer and write it to session.workspace_dir / "flyer.html".

    event_details is expected to contain at least:
      venue_name, venue_address, date, time, party_size, condition,
      temperature_c, total_gbp, deposit_required_gbp

    Write a self-contained HTML flyer (inline CSS, no external assets). Tag every key fact with data-testid="<n>" so the integrity check can parse it.

    Write a formatted HTML flyer with an H1 title, the event
    facts, a weather summary, and the cost breakdown.

    Returns:
      output: {"path": "workspace/flyer.html", "bytes_written": int}
      summary: "generate_flyer: wrote <path> (<N> bytes)"

    MUST call record_tool_call(...) before returning — the integrity
    check compares the flyer's contents against earlier tool outputs.

    IMPORTANT: this tool MUST be registered with parallel_safe=False
    because it writes a file.
    """
    try:
        escaped_details = {
            key: html.escape(str(value)) 
            for key, value in event_details.items()
        }

        template_content = _FLYER_TEMPLATE.read_text(encoding="utf-8")
        html_content = string.Template(template_content).substitute(escaped_details)

        flyer_path = session.workspace_dir / "flyer.html"
        flyer_path.parent.mkdir(parents=True, exist_ok=True)
        
        flyer_path.write_text(html_content, encoding="utf-8")
        bytes_written = flyer_path.stat().st_size
            
        output = dict(
            path=str(flyer_path),
            bytes_written=bytes_written
        )

        record_tool_call(
            tool_name="generate_flyer",
            arguments=dict(event_details=event_details),
            output=output
        )
        
        return ToolResult(
            success=True,
            output=output,
            summary=f"generate_flyer: wrote {flyer_path} ({bytes_written} bytes)"
        )
    except KeyError as exception:
        raise ToolError(_ERR_EXECUTION_FAILED, message=f"Missing key in event_details: {exception}") from exception
    except FileNotFoundError as exception:
        raise ToolError(_ERR_MISSING, message=str(exception)) from exception
    except Exception as exception:
        raise ToolError(_ERR_EXECUTION_FAILED, message=str(exception)) from exception


# ---------------------------------------------------------------------------
# Registry builder — DO NOT MODIFY the name, signature, or registration calls.
# The grader imports and calls this to pick up your tools.
# ---------------------------------------------------------------------------
def build_tool_registry(session: Session, include_builtins: bool = True) -> ToolRegistry:
    """Build a session-scoped tool registry with all four Ex5 tools plus
    the sovereign-agent builtins (read_file, write_file, list_files,
    handoff_to_structured, complete_task).

    DO NOT change the tool names — the tests and grader call them by name.
    """
    if include_builtins:
        from sovereign_agent.tools.builtin import make_builtin_registry
        reg = make_builtin_registry(session)
    else:
        reg = ToolRegistry()

    # venue_search
    reg.register(
        _RegisteredTool(
            name="venue_search",
            description="Search Edinburgh venues by area, party size, and max budget.",
            fn=venue_search,
            parameters_schema={
                "type": "object",
                "properties": {
                    "near": {
                        "type": "string",
                        "description": "Keyword search for the area (e.g., 'Haymarket'). Performs a strict substring match. Do not include full phrases or extra words like 'station'."
                    },
                    "party_size": {"type": "integer"},
                    "budget_max_gbp": {"type": "integer", "default": 1000},
                },
                "required": ["near", "party_size"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"near": "Haymarket", "party_size": 6, "budget_max_gbp": 800},
                    "output": {"count": 1, "results": [{"id": "haymarket_tap"}]},
                }
            ],
        )
    )

    # get_weather
    reg.register(
        _RegisteredTool(
            name="get_weather",
            description="Get scripted weather for a city on a YYYY-MM-DD date.",
            fn=get_weather,
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["city", "date"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"city": "Edinburgh", "date": "2026-04-25"},
                    "output": {"condition": "cloudy", "temperature_c": 12},
                }
            ],
        )
    )

    # calculate_cost
    reg.register(
        _RegisteredTool(
            name="calculate_cost",
            description="Compute total cost and deposit for a booking.",
            fn=calculate_cost,
            parameters_schema={
                "type": "object",
                "properties": {
                    "venue_id": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "duration_hours": {"type": "integer"},
                    "catering_tier": {
                        "type": "string",
                        "enum": ["drinks_only", "bar_snacks", "sit_down_meal", "three_course_meal"],
                        "default": "bar_snacks",
                    },
                },
                "required": ["venue_id", "party_size", "duration_hours"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # pure compute, no shared state
            examples=[
                {
                    "input": {
                        "venue_id": "haymarket_tap",
                        "party_size": 6,
                        "duration_hours": 3,
                    },
                    "output": {"total_gbp": 540, "deposit_required_gbp": 0},
                }
            ],
        )
    )

    # generate_flyer — parallel_safe=False because it writes a file
    def _flyer_adapter(event_details: dict) -> ToolResult:
        return generate_flyer(session, event_details)

    reg.register(
        _RegisteredTool(
            name="generate_flyer",
            description="Write an HTML flyer for the event to workspace/flyer.html.",
            fn=_flyer_adapter,
            parameters_schema={
                "type": "object",
                "properties": {
                    "event_details": {
                        "type": "object",
                        "properties": {
                            "venue_name": {"type": "string"},
                            "venue_address": {"type": "string"},
                            "date": {"type": "string"},
                            "time": {"type": "string"},
                            "party_size": {"type": "integer"},
                            "condition": {"type": "string"},
                            "temperature_c": {"type": "number"},
                            "total_gbp": {"type": "number"},
                            "deposit_required_gbp": {"type": "number"},
                        },
                        "required": [
                            "venue_name", "venue_address", "date", "time", "party_size",
                            "condition", "temperature_c", "total_gbp", "deposit_required_gbp"
                        ]
                    }
                },
                "required": ["event_details"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=False,  # writes a file — MUST be False
            examples=[
                {
                    "input": {
                        "event_details": {
                            "venue_name": "Haymarket Tap",
                            "date": "2026-04-25",
                            "party_size": 6,
                        }
                    },
                    "output": {"path": "workspace/flyer.html"},
                }
            ],
        )
    )

    return reg


__all__ = [
    "build_tool_registry",
    "venue_search",
    "get_weather",
    "calculate_cost",
    "generate_flyer",
]
