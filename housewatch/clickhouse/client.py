from typing import Dict, Optional
from clickhouse_pool import ChPool
from housewatch.clickhouse.queries.sql import EXISTING_TABLES_SQL
from django.core.cache import cache
from django.settings import (
    CLICKHOUSE_HOST,
    CLICKHOUSE_VERIFY,
    CLICKHOUSE_CA,
    CLICKHOUSE_SECURE,
    CLICKHOUSE_DATABASE,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
)
import hashlib
import json


pool = ChPool(
    host=CLICKHOUSE_HOST,
    database=CLICKHOUSE_DATABASE,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    secure=CLICKHOUSE_SECURE,
    ca_certs=CLICKHOUSE_CA,
    verify=CLICKHOUSE_VERIFY,
    settings={"max_result_rows": "2000"},
    send_receive_timeout=30,
)


def run_query(
    query: str,
    params: Dict[str, str | int] = {},
    settings: Dict[str, str | int] = {},
    query_id: Optional[str] = None,
    use_cache: bool = True,  # defaulting to True for now for simplicity, but ideally we should default this to False
    substitute_params: bool = True,
):
    final_query = query % (params or {}) if substitute_params else query
    query_hash = ""

    if use_cache:
        query_hash = hashlib.sha256(final_query.encode("utf-8")).hexdigest()
        cached_result = cache.get(query_hash)
        if cached_result:
            return json.loads(cached_result)
    with pool.get_client() as client:
        result = client.execute(final_query, settings=settings, with_column_types=True, query_id=query_id)
        response = []
        for res in result[0]:
            item = {}
            for index, key in enumerate(result[1]):
                item[key[0]] = res[index]

            response.append(item)
        if use_cache:
            cache.set(query_hash, json.dumps(response, default=str), timeout=60 * 5)
        return response


existing_system_tables = [row["name"] for row in run_query(EXISTING_TABLES_SQL, use_cache=False)]
