#!/usr/bin/python3
from argparse import (
    ArgumentParser,
    Namespace,
    RawDescriptionHelpFormatter,
)
from datetime import datetime
from typing import (
    Iterable,
    List,
)

import matplotlib.pyplot as plt
from matplotlib.dates import (
    DateFormatter,
    MonthLocator,
    YearLocator,
)

from . import (
    from_pypi,
    from_bigquery,
    accumulate,
)


DESCRIPTION = 'Acquire pypi stats for the fixedpoint package.'
EPILOG = f'''\
pypistats.org only keeps 180 days of history. Visit the following site to
obtain more history:

{from_bigquery.BIGQUERY_URL}

You can use the following SQL query to obtain the data:

{from_bigquery.SQL_QUERY}

Once the query returns data, save it in json format to a file and provide that
filename as the JSON argument.

If this filename is not present, then pypistats.org data is used and will only
date back 180 days.
'''


def parse_args(clargs: List = None) -> Namespace:
    '''Parse command line arguments.'''
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=DESCRIPTION,
        epilog=EPILOG,
    )
    parser.add_argument('json',
                        metavar='JSON',
                        help=('json file to parse; run --help to see '
                              'instructions on how to generate it'),
                        nargs='?',
                        default=None)
    ret = parser.parse_args(clargs)
    return ret


def plot(dates: Iterable[str],
         monthly: Iterable[int],
         cum: Iterable[int] = None) -> None:
    '''Generate a plot.'''
    dates_ = [datetime.strptime(d, '%Y-%m') for d in dates]

    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.plot_date(dates_, monthly, '.-')
    if len(dates_) > 12:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    else:
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))

    ax.fmt_xdata = DateFormatter('%Y-%m')
    fig.autofmt_xdate()
    ax.set_title('Monthly fixpoint Downloads')
    plt.xlabel('Month')
    plt.ylabel('# Downloads')
    plt.grid(True)

    if cum is not None:
        ax = fig.add_subplot(212)
        ax.plot_date(dates_, cum, '.-')
        if len(dates_) > 12:
            ax.xaxis.set_major_locator(YearLocator())
            ax.xaxis.set_minor_locator(MonthLocator())
            ax.xaxis.set_major_formatter(DateFormatter('%Y'))
        else:
            ax.xaxis.set_major_locator(MonthLocator())
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))

        ax.fmt_xdata = DateFormatter('%Y-%m')
        fig.autofmt_xdate()
        ax.set_title('Cumulative fixpoint Downloads')
        plt.xlabel('Month')
        plt.ylabel('# Downloads')
        plt.grid(True)

    plt.show()


def main(clargs: List = None) -> None:
    arg = parse_args()

    try:
        stats = from_bigquery.stats_monthly(arg.json)
    except TypeError:
        stats = from_pypi.stats_monthly(arg.json)

    cum = accumulate(stats)

    plot(stats.keys(),
         stats.values(),
         cum.values())


if __name__ == '__main__':
    main()
