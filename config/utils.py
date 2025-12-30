from config.settings import PROJECT_ROOT


def load_graphql_query(query_name: str):
    """
    Loads a GraphQL query from a file based on the provided query name. The function constructs
    the file path using the given query name and reads the content of the file.

    Parameters:
    query_name: str
        The name of the GraphQL query file (without extension).

    Returns:
    str
        The content of the specified GraphQL query file as a string.

    Raises:
    FileNotFoundError
        If the specified query file does not exist.
    """
    query_file = PROJECT_ROOT / "clients" / "grid" / "queries" / f"{query_name}.graphql"
    return query_file.read_text()
