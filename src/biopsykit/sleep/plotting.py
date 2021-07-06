"""Module providing functions to plot data collected during sleep studies."""
from typing import Union, Optional, Dict, Tuple, Sequence, List, Iterable

import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticks

import biopsykit.colors as colors
from biopsykit.utils.datatype_helper import (
    SleepEndpointDict,
    AccDataFrame,
    GyrDataFrame,
    ImuDataFrame,
)

_sleep_imu_plot_params = {
    "background_color": ["#e0e0e0", "#9e9e9e"],
    "background_alpha": [0.3, 0.3],
}

_bbox_default = dict(
    fc=(1, 1, 1, plt.rcParams["legend.framealpha"]),
    ec=plt.rcParams["legend.edgecolor"],
    boxstyle="round",
)


def sleep_imu_plot(
    data: Union[AccDataFrame, GyrDataFrame, ImuDataFrame],
    datastreams: Optional[Union[str, Sequence[str]]] = None,
    sleep_endpoints: Optional[SleepEndpointDict] = None,
    downsample_factor: Optional[int] = None,
    **kwargs,
) -> Tuple[plt.Figure, Iterable[plt.Axes]]:
    """Draw plot to visualize IMU data during sleep, and, optionally, add sleep endpoints information.

    Parameters
    ----------
    data : :class:`~pandas.DataFrame´
        data to plot. Data must either be acceleration data (:obj:`~biopsykit.utils.datatype_helper.AccDataFrame`),
        gyroscope data (:obj:`~biopsykit.utils.datatype_helper.GyrDataFrame`), or IMU data
        (:obj:`~biopsykit.utils.datatype_helper.ImuDataFrame`)
    datastreams : str or list of str, optional
        list of datastreams indicating which type of data should be plotted or ``None`` to only plot acceleration data.
        If more than one type of datastream is specified each datastream is plotted row-wise in its own subplot.
        Default: ``None``
    sleep_endpoints : :obj:`~biopsykit.utils.datatype_helper.SleepEndpointDict`
        dictionary with sleep endpoints to add to plot or ``None`` to only plot IMU data.
    downsample_factor : int, optional
        downsample factor to apply to raw input data before plotting or ``None`` to not downsample data before
        plotting (downsample factor 1). Default: ``None``
    kwargs
        optional arguments for plot configuration.

        To configure which type of sleep endpoint annotations to plot:
            * ``plot_sleep_onset``: whether to plot sleep onset annotations or not: Default: ``True``
            * ``plot_wake_onset``: whether to plot wake onset annotations or not: Default: ``True``
            * ``plot_bed_start``: whether to plot bed interval start annotations or not: Default: ``True``
            * ``plot_bed_end``: whether to plot bed interval end annotations or not: Default: ``True``
            * ``plot_sleep_wake``: whether to plot vspans of detected sleep/wake phases or not: Default: ``True``

        To style general plot appearance:
            * ``axs``: pre-existing axes for the plot. Otherwise, a new figure and axes objects are created and
              returned.
            * ``colormap``: colormap to plot different axes from input data
            * ``figsize``: tuple specifying figure dimensions

        To style axes:
            * ``xlabel``: label of x axis. Default: "Time"
            * ``ylabel``: label of y axis. Default: "Acceleration [$m/s^2$]" for acceleration data and
              "Angular Velocity [$°/s$]" for gyroscope data

        To style legend:
            * ``legend_loc``: location of legend. Default: "lower left"
            * ``legend_fontsize``: font size of legend labels. Default: "smaller"


    Returns
    -------
    fig : :class:`matplotlib.figure.Figure`
        figure object
    axs : list of :class:`matplotlib.axes.Axes`
        list of subplot axes objects

    """
    axs: List[plt.Axes] = kwargs.pop("ax", kwargs.pop("axs", None))
    figsize = kwargs.get("figsize", None)
    sns.set_palette(kwargs.get("colormap", colors.fau_palette_blue("line_3")))

    if datastreams is None:
        datastreams = ["acc"]
    if isinstance(datastreams, str):
        # ensure list
        datastreams = [datastreams]

    if isinstance(axs, plt.Axes):
        # ensure list
        axs = [axs]

    if axs is None:
        fig, axs = plt.subplots(figsize=figsize, nrows=len(datastreams))
    else:
        fig = axs[0].get_figure()

    if downsample_factor is None:
        downsample_factor = 1
    # ensure int
    downsample_factor = int(downsample_factor)
    if downsample_factor < 1:
        raise ValueError("'downsample_factor' must be >= 1!")

    if isinstance(axs, plt.Axes):
        # ensure list (if nrows == 1 only one axes object will be created, not a list of axes)
        axs = [axs]

    if len(datastreams) != len(axs):
        raise ValueError(
            "Number of datastreams to be plotted must match number of provided subplots! Expected {}, got {}.".format(
                len(datastreams), len(axs)
            )
        )

    for ax, ds in zip(axs, datastreams):
        _sleep_imu_plot(
            data=data,
            datastream=ds,
            downsample_factor=downsample_factor,
            sleep_endpoints=sleep_endpoints,
            ax=ax,
            **kwargs,
        )

    fig.tight_layout()
    fig.autofmt_xdate(rotation=0, ha="center")
    return fig, axs


def _sleep_imu_plot(
    data: pd.DataFrame,
    datastream: str,
    downsample_factor: int,
    sleep_endpoints: SleepEndpointDict,
    ax: plt.Axes,
    **kwargs,
):
    legend_loc = kwargs.get("legend_loc", "lower left")
    legend_fontsize = kwargs.get("legend_fontsize", "smaller")
    ylabel = kwargs.get("ylabel", {"acc": "Acceleration [$m/s^2$]", "gyr": "Angular Velocity [$°/s$]"})
    xlabel = kwargs.get("xlabel", "Time")

    if isinstance(data.index, pd.DatetimeIndex):
        plt.rcParams["timezone"] = data.index.tz.zone

    data_plot = data.filter(like=datastream)[::downsample_factor]
    data_plot.plot(ax=ax)
    if sleep_endpoints is not None:
        kwargs.setdefault("ax", ax)
        _sleep_imu_plot_add_sleep_endpoints(sleep_endpoints=sleep_endpoints, **kwargs)

    if isinstance(data_plot.index, pd.DatetimeIndex):
        # TODO add axis style for non-Datetime axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_minor_locator(mticks.AutoMinorLocator(6))

    ax.set_ylabel(ylabel[datastream])
    ax.set_xlabel(xlabel)
    ax.legend(loc=legend_loc, fontsize=legend_fontsize, framealpha=1.0)


def _sleep_imu_plot_add_sleep_endpoints(sleep_endpoints: SleepEndpointDict, **kwargs):
    legend_loc = "lower right"
    legend_fontsize = kwargs.get("legend_fontsize", "smaller")

    bed_start = pd.to_datetime(sleep_endpoints["bed_interval_start"])
    bed_end = pd.to_datetime(sleep_endpoints["bed_interval_end"])
    sleep_onset = pd.to_datetime(sleep_endpoints["sleep_onset"])
    wake_onset = pd.to_datetime(sleep_endpoints["wake_onset"])

    ax = kwargs.get("ax")

    plot_sleep_onset = kwargs.get("plot_sleep_onset", True)
    plot_wake_onset = kwargs.get("plot_wake_onset", True)
    plot_bed_start = kwargs.get("plot_bed_start", True)
    plot_bed_end = kwargs.get("plot_bed_end", True)
    plot_sleep_wake = kwargs.get("plot_sleep_wake", True)

    if isinstance(sleep_endpoints, dict):
        sleep_bouts = sleep_endpoints["sleep_bouts"]
        wake_bouts = sleep_endpoints["wake_bouts"]
        date = sleep_endpoints["date"]
    else:
        sleep_bouts = pd.DataFrame(sleep_endpoints["sleep_bouts"][0])
        wake_bouts = pd.DataFrame(sleep_endpoints["wake_bouts"][0])
        date = sleep_endpoints.index[0][1]

    date = pd.to_datetime(date)

    # 00:00 (12 am) vline (if present)
    if date == bed_start.normalize():
        ax.vlines(
            [date + pd.Timedelta("1d")],
            0,
            1,
            transform=ax.get_xaxis_transform(),
            linewidths=3,
            linestyles="dotted",
            colors=colors.fau_color("tech"),
            zorder=0,
        )

    if plot_sleep_onset:
        _sleep_imu_plot_add_sleep_onset(sleep_onset, **kwargs)
    if plot_wake_onset:
        _sleep_imu_plot_add_wake_onset(wake_onset, **kwargs)
    if plot_bed_start:
        _sleep_imu_plot_add_bed_start(sleep_onset, bed_start, **kwargs)
    if plot_bed_end:
        _sleep_imu_plot_add_bed_end(wake_onset, bed_end, **kwargs)
    if plot_sleep_wake:
        handles = _sleep_imu_plot_add_sleep_wake_bouts(sleep_bouts, wake_bouts, **kwargs)
        legend = ax.legend(
            handles=list(handles.values()),
            labels=list(handles.keys()),
            loc=legend_loc,
            fontsize=legend_fontsize,
            framealpha=1.0,
        )
        ax.add_artist(legend)

    # wear_time['end'] = wear_time.index.shift(1, freq=pd.Timedelta("15M"))
    # wear_time = wear_time[wear_time['wear'] == 0.0]
    # wear_time = wear_time.reset_index()
    #
    # handle = None
    # for idx, row in wear_time.iterrows():
    #     handle = ax.axvspan(row['index'], row['end'], color=colors.fau_color('wiso'), alpha=0.5, lw=0)
    # if handle is not None:
    #     handles['non-wear'] = handle

    ax.set_title("Sleep IMU Data: {} – {}".format(date.date(), (date + pd.Timedelta("1d")).date()))


def _sleep_imu_plot_add_sleep_onset(sleep_onset, **kwargs):
    ax = kwargs.get("ax")
    bbox = kwargs.get("bbox", _bbox_default)

    # Sleep Onset vline
    ax.vlines(
        [sleep_onset],
        0,
        1,
        transform=ax.get_xaxis_transform(),
        linewidth=3,
        linestyles="--",
        colors=colors.fau_color("nat"),
        zorder=3,
    )

    # Sleep Onset Text + Arrow
    ax.annotate(
        "Sleep Onset",
        xy=(mdates.date2num(sleep_onset), 0.90),
        xycoords=ax.get_xaxis_transform(),
        xytext=(mdates.date2num(sleep_onset + pd.Timedelta("20min")), 0.90),
        textcoords=ax.get_xaxis_transform(),
        ha="left",
        va="center",
        bbox=bbox,
        size=14,
        arrowprops=dict(
            arrowstyle="->",
            lw=2,
            color=colors.fau_color("nat"),
            shrinkA=0.0,
            shrinkB=0.0,
        ),
    )


def _sleep_imu_plot_add_wake_onset(wake_onset, **kwargs):
    ax = kwargs.get("ax")
    bbox = kwargs.get("bbox", _bbox_default)
    # Wake Onset vline
    ax.vlines(
        [wake_onset],
        0,
        1,
        transform=ax.get_xaxis_transform(),
        linewidth=3,
        linestyles="--",
        colors=colors.fau_color("nat"),
        zorder=3,
    )

    # Wake Onset Text + Arrow
    ax.annotate(
        "Wake Onset",
        xy=(mdates.date2num(wake_onset), 0.90),
        xycoords=ax.get_xaxis_transform(),
        xytext=(mdates.date2num(wake_onset - pd.Timedelta("20min")), 0.90),
        textcoords=ax.get_xaxis_transform(),
        ha="right",
        va="center",
        bbox=bbox,
        size=14,
        arrowprops=dict(
            arrowstyle="->",
            lw=2,
            color=colors.fau_color("nat"),
            shrinkA=0.0,
            shrinkB=0.0,
        ),
    )


def _sleep_imu_plot_add_bed_start(sleep_onset, bed_start, **kwargs):
    ax = kwargs.get("ax")
    bbox = kwargs.get("bbox", _bbox_default)

    # Bed Start vline
    ax.vlines(
        [bed_start],
        0,
        1,
        transform=ax.get_xaxis_transform(),
        linewidth=3,
        linestyles="--",
        colors=colors.fau_color("med"),
        zorder=3,
    )
    # Bed Start Text + Arrow
    ax.annotate(
        "Bed Interval Start",
        xy=(mdates.date2num(bed_start), 0.80),
        xycoords=ax.get_xaxis_transform(),
        xytext=(mdates.date2num(sleep_onset + pd.Timedelta("20min")), 0.80),
        textcoords=ax.get_xaxis_transform(),
        ha="left",
        va="center",
        bbox=bbox,
        size=14,
        arrowprops=dict(
            arrowstyle="->",
            lw=2,
            color=colors.fau_color("med"),
            shrinkA=0.0,
            shrinkB=0.0,
        ),
    )


def _sleep_imu_plot_add_bed_end(wake_onset, bed_end, **kwargs):
    ax = kwargs.get("ax")
    bbox = kwargs.get("bbox", _bbox_default)

    # Bed End vline
    ax.vlines(
        [bed_end],
        0,
        1,
        transform=ax.get_xaxis_transform(),
        linewidth=3,
        linestyles="--",
        colors=colors.fau_color("med"),
        zorder=3,
    )
    # Bed End Text + Arrow
    ax.annotate(
        "Bed Interval End",
        xy=(mdates.date2num(bed_end), 0.80),
        xycoords=ax.get_xaxis_transform(),
        xytext=(mdates.date2num(wake_onset - pd.Timedelta("20min")), 0.80),
        textcoords=ax.get_xaxis_transform(),
        ha="right",
        va="center",
        bbox=bbox,
        size=14,
        arrowprops=dict(
            arrowstyle="->",
            lw=2,
            color=colors.fau_color("med"),
            shrinkA=0.0,
            shrinkB=0.0,
        ),
    )


def _sleep_imu_plot_add_sleep_wake_bouts(
    sleep_bouts: pd.DataFrame, wake_bouts: pd.DataFrame, **kwargs
) -> Dict[str, plt.Artist]:
    ax = kwargs.get("ax")
    handles = {}
    for (bout_name, bouts), bg_color, bg_alpha in zip(
        {"sleep": sleep_bouts, "wake": wake_bouts}.items(),
        kwargs.get("background_color", _sleep_imu_plot_params["background_color"]),
        kwargs.get("background_alpha", _sleep_imu_plot_params["background_alpha"]),
    ):
        handle = None
        for _, bout in bouts.iterrows():
            handle = ax.axvspan(bout["start"], bout["end"], color=bg_color, alpha=bg_alpha)

        handles[bout_name] = handle

    handles = {k: v for k, v in handles.items() if v is not None}
    return handles
