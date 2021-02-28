import io
from collections import defaultdict
from time import struct_time, strftime
from typing import List, Tuple

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

from open_weather_api import Weather

emoji_font = font_manager.FontProperties(fname='/home/bnavras/Downloads/emoji.ttf')
mpl.rcParams['axes.formatter.useoffset'] = False

def get_weather_chart(weathers: List[Tuple[struct_time, Weather]]):
    temperatures, emojis, time_labels = [], [], []

    day = None
    for time, weather in weathers:
        temperatures.append(weather.temperature)
        emojis.append(weather.icon)

        if time.tm_wday != day:
            label = strftime('%H:%M\n%A', time)
            day = time.tm_wday
        else:
            label = strftime('%H:%M', time)

        time_labels.append(label)

    fig, ax = plt.subplots()
    fig.set_size_inches(20, 8)

    x_ticks = [i + 0.5 for i in range((len(weathers)))]
    ax.xaxis.set_ticks(x_ticks)
    ax.xaxis.set_ticklabels(time_labels, fontsize=15)
    ax.tick_params(axis='y', labelsize=15)
    for i in range(len(weathers)):
        plt.axvspan(i, i+1, facecolor=['w', 'black'][i % 2], alpha=0.2)

    ax_t = ax.secondary_xaxis('top')
    ax_t.xaxis.set_ticks(x_ticks)
    ax_t.xaxis.set_tick_params(length=0)
    ax_t.xaxis.set_ticklabels(emojis, fontproperties=emoji_font, fontsize=50)

    plt.plot(x_ticks, temperatures, 'r-o')
    plt.gca().axes.get_yaxis().set_visible(False)
    last_annotation = ''
    for i, j in zip(x_ticks, temperatures):
        current_temperature = str(j)
        annotation = current_temperature if last_annotation != current_temperature else ''
        last_annotation = current_temperature
        ax.annotate(annotation, xy=(i, j), xytext=(-7, 7), textcoords='offset points', fontsize=20)

    buf = io.BytesIO()
    plt.savefig(buf, bbox_inches='tight', format='png')
    plt.close()
    buf.seek(0)
    buf.name = '123.png'
    return buf


def get_weather_boxplot(weathers: List[Tuple[struct_time, Weather]]):
    grouped_forecast = defaultdict(list)
    for time, weather in weathers:
        label = strftime('%d.%m', time)
        grouped_forecast[label].append(weather)

    time_labels = list(grouped_forecast.keys())
    grouped_weathers = grouped_forecast.values()
    emojis = [g[0].icon for g in grouped_weathers]
    temperatures = [[w.temperature for w in group] for group in grouped_weathers]
    medians = [np.median(t) for t in temperatures]

    fig, ax = plt.subplots()
    fig.set_size_inches(20, 8)

    x_ticks = [i + 0.5 for i in range((len(grouped_weathers)))]
    ax.xaxis.set_ticks(x_ticks)
    ax.xaxis.set_ticklabels(time_labels, fontsize=15)
    ax.tick_params(axis='y', labelsize=15)

    for i in range(len(grouped_weathers)):
        plt.axvspan(i, i + 1, facecolor=['w', 'black'][i % 2], alpha=0.2)

    plt.boxplot(temperatures, labels=time_labels, positions=x_ticks, manage_ticks=False)
    plt.plot(x_ticks, medians, 'r-o', linestyle='--', dashes=(5, 5), alpha=0.5)
    for i, j in zip(x_ticks, medians):
        ax.annotate(str(round(j)), xy=(i, j), xytext=(-7, 7), textcoords='offset points', fontsize=20)

    ax_t = ax.twiny()
    ax_t.set_xlim(ax.get_xlim())
    ax_t.xaxis.set_ticks(x_ticks)
    ax_t.xaxis.set_tick_params(length=0)
    ax_t.xaxis.set_ticklabels(emojis, fontproperties=emoji_font, fontsize=50)

    buf = io.BytesIO()
    plt.savefig(buf, bbox_inches='tight', format='png')
    plt.close()
    buf.seek(0)
    buf.name = '123.png'
    return buf
