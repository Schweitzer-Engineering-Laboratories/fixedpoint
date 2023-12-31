import itertools
from typing import Dict


def accumulate(monthly_data: Dict[str, int]) -> Dict[str, int]:
    '''Take the given monthly data and generate cumulative data.'''
    acums = itertools.accumulate(monthly_data.values())
    return dict(zip(monthly_data.keys(), acums))
