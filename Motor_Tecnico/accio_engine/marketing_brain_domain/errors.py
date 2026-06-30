class MarketingBrainError(Exception):
    pass


class LLMUnavailable(MarketingBrainError):
    pass


class EnrichmentParseError(MarketingBrainError):
    pass
