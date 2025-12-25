class GridError(Exception):
    """Base exception for GRID client"""
    pass


class GridAuthError(GridError):
    pass


class GridRateLimitError(GridError):
    pass


class GridGraphQLError(GridError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("GraphQL execution failed", errors)
