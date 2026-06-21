"""Smoke test for vnpy_ai.tools and vnpy_ai.utils imports."""

print("Testing vnpy_ai.tools imports...")
from vnpy_ai.tools.api import (
    get_financial_metrics,
    get_market_cap,
    get_prices,
    prices_to_df,
    search_line_items,
    set_data_adapter,
)
print("  tools.api OK")

from vnpy_ai.tools import (
    get_financial_metrics as _gfm,
    set_data_adapter as _sda,
)
print("  tools __init__ OK")

print("Testing vnpy_ai.utils imports...")
from vnpy_ai.utils.llm import call_llm, create_default_response
print("  utils.llm OK")

from vnpy_ai.utils.api_key import (
    get_api_key_from_state,
    mask_api_key,
    get_api_key_from_env,
)
print("  utils.api_key OK")

from vnpy_ai.utils.analysts import ANALYST_CONFIG, ANALYST_ORDER, get_agents_list
print("  utils.analysts OK")

from vnpy_ai.utils.progress import progress, AgentProgress
print("  utils.progress OK")

from vnpy_ai.utils.display import print_trading_output, format_backtest_row
print("  utils.display OK")

from vnpy_ai.utils.visualize import save_graph_as_png
print("  utils.visualize OK")

print("Testing functional checks...")

# API key masking
assert mask_api_key(None) is None
assert mask_api_key("short") == "****"
assert mask_api_key("sk-1234567890abcdef") == "sk-****cdef"
print("  mask_api_key OK")

# Analyst config has 19 entries
assert len(ANALYST_CONFIG) == 19, f"Expected 19 analysts, got {len(ANALYST_CONFIG)}"
print(f"  ANALYST_CONFIG has {len(ANALYST_CONFIG)} entries OK")

# get_agents_list returns ordered list
agents_list = get_agents_list()
assert len(agents_list) == 19
assert agents_list[0]["order"] == 0
assert agents_list[-1]["order"] == 18
print("  get_agents_list ordering OK")

# prices_to_df on empty list
df = prices_to_df([])
assert df.empty
print("  prices_to_df empty OK")

# call_llm default response
from pydantic import BaseModel


class _DummyModel(BaseModel):
    name: str
    score: float
    count: int


default = create_default_response(_DummyModel)
assert isinstance(default, _DummyModel)
print("  create_default_response OK")

print("\nAll smoke tests passed.")
