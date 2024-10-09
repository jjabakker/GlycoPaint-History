


def calc_average_track_count_of_lowest_squares(df_squares, nr_of_average_count_squares):
    """
    The function calculates the average track count of the lowest average_count_squares squares with a track count > 0.
    The df_squares df is already sorted on track number.
    All we have to do is access backwards, ignore 0 values and only then start counting.

    :param df_squares:
    :param nr_of_average_count_squares:
    :return:
    """

    count_values = list(df_squares['Nr Tracks'])

    total = 0
    n = 0
    for i in range(len(count_values) - 1, 0, -1):
        if count_values[i] > 0:
            total += count_values[i]
            n += 1
            if n >= nr_of_average_count_squares:
                break
    if n == 0:
        average = 0
    else:
        average = total / n
    return average