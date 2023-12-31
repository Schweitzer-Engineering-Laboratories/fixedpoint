'''Fixedpoint package downloads statistics from pypi.

This uses pypistats (https://pypistats.org/) to gather statistics on
the last 180 days.
'''
from datetime import date, datetime, timedelta
import json
from typing import (
    Any,
    List,
    Dict,
)
import warnings

import pypistats as pps
from prodict import Prodict


class CategoryDownloads(Prodict):
    downloads: int


class Stats(Prodict):
    data: List[CategoryDownloads]


# Suppress 180-day warning issued by pypistats
warnings.simplefilter("ignore", UserWarning)


def stats_monthly(*args: Any, **kwargs: Any) -> Dict[str, int]:
    '''Get monthly pypi download stats.

    Returns:
        Ordered dict of monthy downloads, keyed by yyyy-mm date string
        and valued by the number of downloads that month.
    '''
    TODAY = date.today()
    ONE_DAY = timedelta(days=1)
    ret = {}
    query = Prodict(format='json', color='no')
    for year in range(2020, TODAY.year + 1):
        for month in range(12):

            # Determine start and end dates
            startdt = datetime.strptime(
                f'{year}-{month + 1:02d}-01',
                '%Y-%m-%d')
            next_month = (month + 1) % 12
            nextmonthdt = datetime.strptime(
                f'{year}-{next_month + 1:02d}-01',
                '%Y-%m-%d')
            enddt = nextmonthdt - ONE_DAY
            query.start_date = startdt.strftime('%Y-%m-%d')
            query.end_date = enddt.strftime('%Y-%m-%d')

            # Get data
            try:
                response = pps.overall('fixedpoint', **query)
            except ValueError:
                continue

            # Format data
            raw = Stats.from_dict(json.loads(response))

            # Parse Data
            key = f'{year}-{month + 1:02d}'
            ret[key] = max(raw.data[0].downloads,
                           raw.data[1].downloads)

    return ret
