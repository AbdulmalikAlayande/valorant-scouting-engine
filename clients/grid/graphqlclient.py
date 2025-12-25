import json
import requests
from pathlib import Path
from clients.grid.exceptions import (GridError, GridAuthError, GridGraphQLError, GridRateLimitError)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class GraphQLClient:

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout


    def execute(self, query: str, variables: dict | None = None):

        payload = {
            "query": query,
            "variables": variables or {}
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

        response = requests.post(self.base_url, json=payload, headers=headers, timeout=self.timeout)

        if response.status_code == 401 or response.status_code == 403:
            raise GridAuthError("Invalid or missing GRID API key")

        if response.status_code == 429:
            raise GridRateLimitError("GRID rate limit exceeded")

        if not response.ok:
            raise GridError(
                f"HTTP error {response.status_code}: {response.text}"
            )

        result = response.json()

        if "errors" in result:
            errors = result["errors"]
            print(errors)
            error_file = PROJECT_ROOT / "errors" / "graphql-errors.json"
            error_file.parent.mkdir(parents=True, exist_ok=True)
            with open(error_file, "w") as f:
                json.dump(errors, f, indent=4)
            raise GridGraphQLError(errors=errors)

        return result["data"]