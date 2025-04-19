import io
from time import struct_time, strftime
from typing import List, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

from .open_weather_api import Weather

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
    ax.xaxis.set_ticklabels(time_labels, fontsize=20)
    for i in range(len(weathers)):
        plt.axvspan(i, i+1, facecolor=['w', 'black'][i % 2], alpha=0.2)

    ax_t = ax.secondary_xaxis('top')
    ax_t.xaxis.set_ticks(x_ticks)
    ax_t.xaxis.set_tick_params(length=0)
    ax_t.xaxis.set_ticklabels(emojis, fontproperties=emoji_font, fontsize=50)

    plt.gca().axes.get_yaxis().set_visible(False)
    plt.plot(x_ticks, temperatures, 'r-o')
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
    day_weathers = [i for i in weathers if i[0].tm_hour == 13]
    time_labels = [strftime('%d.%m', d) for (d, _) in day_weathers]
    emojis = [w.icon for (_, w) in day_weathers]
    day_temperatures = [weather.temperature for (time, weather) in day_weathers]

    fig, ax = plt.subplots()
    fig.set_size_inches(20, 8)

    x_ticks = [i + 0.5 for i in range((len(day_weathers)))]
    ax.xaxis.set_ticks(x_ticks)
    ax.xaxis.set_ticklabels(time_labels, fontsize=20)
    for i in range(len(day_weathers)):
        plt.axvspan(i, i + 1, facecolor=['w', 'black'][i % 2], alpha=0.2)

    ax_t = ax.secondary_xaxis('top')
    ax_t.xaxis.set_ticks(x_ticks)
    ax_t.xaxis.set_tick_params(length=0)
    ax_t.xaxis.set_ticklabels(emojis, fontproperties=emoji_font, fontsize=50)

    plt.gca().axes.get_yaxis().set_visible(False)
    plt.plot(x_ticks, day_temperatures, 'r-o', label='днем')
    last_annotation = ''
    for i, j in zip(x_ticks, day_temperatures):
        current_temperature = str(round(j))
        annotation = current_temperature if last_annotation != current_temperature else ''
        last_annotation = current_temperature
        ax.annotate(annotation, xy=(i, j), xytext=(-7, 7), textcoords='offset points', fontsize=20)

    buf = io.BytesIO()
    plt.savefig(buf, bbox_inches='tight', format='png')
    plt.close()
    buf.seek(0)
    buf.name = '123.png'
    return buf
