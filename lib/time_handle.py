
def seconds_to_text(seconds):
    time_values = {'year': 3600 * 24 * 365,
                   'month': 3600 * 24 * 31,
                   'week': 3600 * 24 * 7,
                   'day': 3600 * 24,
                   'hour': 3600,
                   'minute': 60,
                   'second': 1
                   }

    rest = seconds
    end = []
    for key, value in time_values.items():
        if rest >= value:
            amount = int(rest // value)
            rest = rest % value
            if amount == 1:
                end.append(f'{amount} {key}')
            else:
                end.append(f'{amount} {key}s')

    if len(end) > 1:
        endstring = ', '.join(end[:-1])
        endstring += f' and {end[-1]}'
    elif len(end) > 0:
        endstring = end[0]
    else:
        endstring = '0 seconds'

    return endstring