'''Fixedpoint package downloads statistics from BigQuery.

pypistats (https://pypistats.org/) only keeps statistics from the last
180 days, so to get all-time download history, Google Cloud's BigQuery
pypi downloads tables must be used.

To do this, navigate to
https://bigquery.cloud.google.com/table/bigquery-public-data:pypi.downloads
and use query shown in the SQL_QUERY parameter in this module.

Export/copy the data as a json file and use this script to point to it.
'''
import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    Union,
)

BIGQUERY_URL = 'https://bigquery.cloud.google.com/table/bigquery-public-data:pypi.downloads'  # noqa
SQL_QUERY = '''\
#standardSQL
SELECT
  COUNT(*) AS num_downloads,
  DATE_TRUNC(DATE(timestamp), MONTH) AS `month`
FROM `bigquery-public-data.pypi.file_downloads`
WHERE
  file.project = 'fixedpoint'
  AND DATE(timestamp)
    BETWEEN '2020-04-01' -- fixedpoint 1.0.0 published on this date
    AND CURRENT_DATE()
GROUP BY `month`
ORDER BY `month` ASC'''


def stats_monthly(filename: Union[str, Path],
                  *args: Any,
                  **kwargs: Any) -> Dict[str, int]:
    '''Get monthly pypi download stats from BigQuery data.

    Args:
        filename: path to json-formatted file of BigQuery results.

    Returns:
        Ordered dict of monthy downloads, keyed by yyyy-mm date string
        and valued by the number of downloads that month.

    File contents must be ordered (per SQL_QUERY) and in the following format:
    [
        {
            "num_downloads": "42",
            "month": " 2020-04-01"
        },
        ...
    ]
    '''
    # Load json file
    with open(filename) as fp:
        data = json.load(fp)
    return {entry["month"][:-3]: int(entry["num_downloads"]) for entry in data}
