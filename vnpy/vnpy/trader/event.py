"""
Event type string used in the trading platform.
"""

from vnpy.event import EVENT_TIMER  # noqa

EVENT_TICK = "eTick."
EVENT_BAR = "eBar."
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_QUOTE = "eQuote."
EVENT_CONTRACT = "eContract."
EVENT_LOG = "eLog"

EVENT_AI_SIGNAL = "eAiSignal"
EVENT_AI_DECISION = "eAiDecision"
EVENT_AI_DECISION_ORDER = "eAiDecisionOrder"
EVENT_AI_ERROR = "eAiError"
EVENT_AI_STATUS = "eAiStatus"
