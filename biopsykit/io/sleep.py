from ast import literal_eval
from pathlib import Path
from typing import Optional, Union, Dict, Sequence

import pytz
import pandas as pd
import numpy as np

from biopsykit._types import path_t
from biopsykit.utils.time import tz

__all__ = [
    'load_withings_sleep_analyzer_raw_file',
    'load_withings_sleep_analyzer_raw_folder',
    'load_withings_sleep_analyzer_summary',
]

RAW_DATA_SOURCES = {
    'hr': 'heart_rate',
    'respiratory-rate': 'respiration_rate',
    'sleep-state': 'sleep_state',
    'snoring': 'snoring'
}
""" suffix in filename : name of biosignal (and name of dataframe column) """


def load_withings_sleep_analyzer_raw_folder(folder_path: path_t,
                                            timezone: Optional[Union[pytz.timezone, str]] = tz,
                                            split_nights: Optional[bool] = True) -> Union[
    pd.DataFrame, Sequence[pd.DataFrame]]:
    import biopsykit.sleep.utils as utils
    """

    Parameters
    ----------
    folder_path
    timezone

    Returns
    -------
    columns:
    heart_rate
    respiration_rate
    sleep_state: 0 = awake, 1 = light sleep, 2 = deep sleep, 3 = rem sleep
    snoring: 0 = no snoring, 100 = snoring

    """
    import re
    # ensure pathlib
    folder_path = Path(folder_path)
    raw_files = list(sorted(folder_path.glob("raw_sleep-monitor_*.csv")))
    data_sources = [re.findall(r"raw_sleep-monitor_(\S*).csv", s.name)[0] for s in raw_files]

    list_data = [load_withings_sleep_analyzer_raw_file(file_path, RAW_DATA_SOURCES[data_source], timezone)
                 for file_path, data_source in zip(raw_files, data_sources) if data_source in RAW_DATA_SOURCES]
    data = pd.concat(list_data, axis=1)
    if split_nights:
        data = utils.split_nights(data)
        data = [d.resample("1min").interpolate() for d in data]
    return data


def load_withings_sleep_analyzer_raw_file(file_path: path_t, data_source: str,
                                          timezone: Optional[Union[pytz.timezone, str]] = tz) -> pd.DataFrame:
    if data_source not in RAW_DATA_SOURCES.values():
        raise ValueError(
            "Unsupported data source {}! Must be one of {}.".format(data_source, list(RAW_DATA_SOURCES.values())))

    data = pd.read_csv(file_path)
    # convert string timestamps to datetime
    data['start'] = pd.to_datetime(data['start'])
    # convert strings of arrays to arrays
    data['duration'] = data['duration'].apply(literal_eval)
    data['value'] = data['value'].apply(literal_eval)
    # set index and sort
    data = data.set_index('start').sort_index()
    # rename index
    data.index.name = 'time'
    # explode data and apply timestamp explosion to groups
    data_explode = data.apply(pd.Series.explode)
    data_explode = data_explode.groupby('time', group_keys=False).apply(_explode_timestamp)
    # convert it into the right time zone
    data_explode = data_explode.tz_localize('UTC').tz_convert(timezone)
    # rename the value column
    data_explode.columns = [data_source]
    # convert dtypes from object into numerical values
    data_explode = data_explode.astype(int)
    # sort index and drop duplicate index values
    data_explode = data_explode.sort_index()
    data_explode = data_explode[~data_explode.index.duplicated()]
    return data_explode


def load_withings_sleep_analyzer_summary(file_path: path_t) -> pd.DataFrame:
    data = pd.read_csv(file_path)

    for col in ['von', 'bis']:
        # convert into date time
        data[col] = pd.to_datetime(data[col])

    # total duration in seconds
    data['total_duration'] = [int(td.total_seconds()) for td in (data['bis'] - data['von'])]
    data['time'] = data['von']

    data.rename({
        'leicht (s)': 'total_time_light_sleep',
        'tief (s)': 'total_time_deep_sleep',
        'rem (s)': 'total_time_rem_sleep',
        'wach (s)': 'total_time_awake',
        'Aufwachen': 'num_wake_bouts',
        'Duration to sleep (s)': 'sleep_onset_latency',
        'Duration to wake up (s)': 'getup_latency',
        'Snoring episodes': 'count_snoring_episodes',
        'Snoring (s)': 'total_time_snoring',
        'Average heart rate': 'heart_rate_avg',
        'Heart rate (min)': 'heart_rate_min',
        'Heart rate (max)': 'heart_rate_max'
    }, axis='columns', inplace=True)

    data['sleep_onset'] = data['time'] + pd.to_timedelta(data['sleep_onset_latency'], unit='seconds')
    # Wake after Sleep Onset (WASO): total time awake after sleep onset
    data['wake_after_sleep_onset'] = data['total_time_awake'] - data['sleep_onset_latency'] - data['getup_latency']
    data['wake_onset'] = data['bis'] - pd.to_timedelta(data['getup_latency'], unit='seconds')
    # compute total sleep duration
    # = total duration - (time to fall asleep + time to get up (= time spent in bed after waking up))
    data['total_sleep_duration'] = data['total_duration'] - data['sleep_onset_latency'] - data['getup_latency']

    transform_cols = ['total_time_light_sleep', 'total_time_deep_sleep', 'total_time_rem_sleep', 'total_time_awake',
                      'sleep_onset_latency', 'getup_latency', 'total_time_snoring', 'wake_after_sleep_onset',
                      'total_sleep_duration']
    data[transform_cols] = data[transform_cols].transform(lambda column: (column / 60).astype(int))

    data.drop(columns=['von', 'bis'], inplace=True)
    data.set_index('time', inplace=True)

    # reindex column order
    new_cols = list(data.columns)
    sowo = ['sleep_onset', 'wake_onset']
    for d in sowo:
        new_cols.remove(d)
    data = data[sowo + new_cols]
    return data


def save_sleep_data(file_path: path_t, data: pd.DataFrame):
    data.to_csv(file_path)


def save_sleep_endpoints(file_path: path_t, df_or_dict: Union[pd.DataFrame, Dict]) -> None:
    if isinstance(df_or_dict, pd.DataFrame):
        df_or_dict.to_csv(file_path)
    else:
        # TODO save dict as json
        raise NotImplementedError(
            "Exporting sleep endpoint dictionary not implemented yet! Consider importing sleep endpoints as dataframe.")


def load_sleep_data(file_path: path_t) -> pd.DataFrame:
    data = pd.read_csv(file_path, index_col=['time'])
    return data


def _explode_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    # sum up the time durations and subtract the first value from it (so that we start from 0)
    # dur_sum then looks like this: [0, 60, 120, 180, ...]
    dur_sum = df['duration'].cumsum() - df['duration'].iloc[0]
    # Add these time durations to the index timestamps.
    # For that, we need to convert the datetime objects from the pandas DatetimeIndex into a float
    # and add the time onto it (we first need to multiply it with 10^9 because the time in the index
    # is stored in nanoseconds)
    index_sum = df.index.values.astype(float) + 1e9 * dur_sum
    # convert the float values back into a DatetimeIndex
    df['time'] = pd.to_datetime(index_sum)
    # set this as index
    df.set_index('time', inplace=True)
    # we don't need the duration column anymore so we can drop it
    df.drop(columns='duration', inplace=True)
    return df
