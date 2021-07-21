import pandas as pd
import os
import matplotlib.pyplot as plt


def data_path(i):

    """
    Returns path to video data

    @param i: video file number
    @return: path to video
    """

    HOME = os.getcwd()
    return HOME + '/_data/dsc_homework_video_{}.csv'.format(i)


def data_path_jup(i):

    """
    Returns path to video data when executing in Jupyter notebook

    @param i: video file number
    @return: path to video
    """

    return '../_data/dsc_homework_video_{}.csv'.format(i)


def remove_duplicates(df_input):

    """
    Removes duplicates

    @param df_input: input dataframe
    @return: a copy without duplicates
    """

    df = df_input.copy()
    size_i = df.shape[0]

    cols = ['video_id', 'subject_id', 'frame_no', 'millisecond_from_start',
               'positive_1', 'positive_2', 'negative_1', 'negative_2', 'negative_3']
    df.drop_duplicates(cols, inplace=True)

    cols = ['video_id', 'subject_id', 'millisecond_from_start',
               'positive_1', 'positive_2', 'negative_1', 'negative_2', 'negative_3']
    df.drop_duplicates(cols, inplace=True)

    size_f = df.shape[0]
    print('{} ({}%) duplicates dropped'.format(size_i - size_f, round((size_i - size_f)/size_i*100,1)))

    return df


def load_data(path):

    """
    Loads video data

    @param path: path to a video file
    @return: dataframes, corresponding to each video + a full dataframe
    """

    print('Load data')

    df1 = pd.read_csv(path(1))
    df2 = pd.read_csv(path(2))
    df3 = pd.read_csv(path(3))
    for df in [df1, df2, df3]:
        df = remove_duplicates(df)

    df = pd.concat([df1, df2, df3], ignore_index=True)

    print('Data loaded \n')

    return df, df1, df2, df3


def no_value(df_input):

    """
    Shows non-numeric values and its count

    @param df_input: input dataframe
    """

    df = df_input.copy()

    for column in df.columns:
        idx = pd.to_numeric(df[column], errors='coerce').isna()
        no_val = list(set(df[idx][column]))
        no_val_len = len(df[idx][column])
        print(no_val, "{}%".format(round(no_val_len / df.shape[0] * 100)))


def replace_no_value_id_sub(df_input, method='preceding'):

    """
    Replaces 'No value' in video_id & subject_id in df_input. This function is an auxiliary function and is used in
    replace_no_value_id.

    @param df_input: input dataframe
    @param method: 'preceding' or 'following'; replace by the preceding or next column value
    @return: a dataframe with replaced mising values
    """

    df = df_input.copy()
    for c in ['video_id', 'subject_id']:
        df[c] = pd.to_numeric(df[c], errors='coerce', downcast='integer')
        if method == 'preceding':
            df[c].fillna(method='ffill', inplace=True)
        if method == 'following':
            df[c].fillna(method='bfill', inplace=True)
        df[c] = df[c].astype('int32').astype('str')

    return df


def replace_no_value_id(df_input):

    """
        Replace 'No value' entries by preceding/following value if the 'frame_no' changes by 1 with respect to
        previous/next value.

        @param df_input: input dataframe
        @return:a dataframe with replaced missing values
    """

    df = df_input.copy()

    # label missing entries
    df['no_value'] = df['no_value_id']

    # restrict data frame to missing + neighbour values
    df = df[(df['no_value'] == 1) | (df['no_value'].shift() == 1) | (df['no_value'].shift(-1) == 1)]

    # count consecutive missing entries (=1); e.g., [0,0,1,0,1,1,0,0] will correspond to [0,0,1,0,2,2,0,0]
    group = df.groupby((df['no_value'] != df['no_value'].shift()).cumsum())
    df['no_value_count'] = group['no_value'].transform('sum')

    # replace missing values by preceding value
    df = replace_no_value_id_sub(df, 'preceding')

    # compute difference between current and previous value for 'frame_no'
    df['frame_no_diff'] = df.groupby(['subject_id'])['frame_no'].transform(lambda x: x.diff().abs())

    # if any of frame_no_diff in a group of consequent missing values not eq 1 => label the whole group with this value
    group = df.groupby((df['no_value'] != df['no_value'].shift()).cumsum())
    df['frame_no_diff'] = group['frame_no_diff'].transform('max')

    # if frame number did not change by 1, change back to 'No value'
    for c in ['video_id', 'subject_id']:
        df.loc[(df['frame_no_diff'] != 1) & (df['no_value'] == 1), c] = 'No value'

    # label missing entries
    df['no_value'] = (df['subject_id'] == 'No value').astype('int')

    # replace missing values by following value
    df = replace_no_value_id_sub(df, 'following')

    # compute difference between current and following value for 'frame_no'
    df['frame_no_diff'] = df.groupby(['subject_id'])['frame_no'].transform(lambda x: x.diff().abs().shift(-1))

    # if frame number did not change by 1, change back to 'No value'
    for c in ['video_id', 'subject_id']:
        df.loc[(df['frame_no_diff'] != 1) & (df['no_value'] == 1), c] = 'No value'

    if set(df[df['no_value'] == 1]['frame_no_diff']) == {1}:
        print('All id missing values were successfully replaced \n')
    else:
        print('Not all missing values were replaced. Investigate manually! \n')

    return df[df.columns[:-3]]


def plot_no_value_emotion(df_input):

    """
        Plots statistics on missing emotion values

        @param df_input: input dataframe
    """

    df = df_input.copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 7))
    fig.suptitle("Missing emotion values distribution", fontsize=20)

    # total per video
    group = df.groupby('video_id')['no_value_emotion']
    x = group.value_counts().unstack()
    x = x.divide(x.sum(axis=1)/100, axis=0).round(1)

    ax1.set_title('per video', fontsize=15)
    ax1.set(xlabel='Video ID', ylabel='Frequency, %')
    x[1].plot(ax=ax1, kind='bar', rot=0)

    # total per subject
    group = df.groupby('subject_id')['no_value_emotion']
    x = group.value_counts().unstack()
    x = x.divide(x.sum(axis=1)/100, axis=0).round(1)
    x = x.fillna(0).astype('int32')
    x['cat'] = pd.cut(x[1], bins=5, labels=None)
    x = x['cat'].value_counts().sort_index()
    x = x.divide(x.sum()/100).round(1)

    ax2.set_title('per subject', fontsize=15)
    ax2.set(xlabel='Proportion of missing values per subject, category', ylabel='Frequency, %')
    x.plot(ax=ax2, kind='bar', rot=0)

    # display bar values
    for ax in (ax1, ax2):
        for p in ax.patches:
            ax.annotate(str(p.get_height()), (p.get_x()+p.get_width()/2., p.get_y()+p.get_height()/2.),
                        ha='center', va='center')


def remove_subjects_no_value_emotion(df_input, threshold=30):

    """
    Drops subjects with proportion of missing emotion data greater then a given threshold

    @param df_input: input dataframe
    @param threshold: number
    @return: a dataframe without dropped subjects
    """

    df = df_input.copy()

    # calculate proportion of missing emotion data for each subject
    group = df.groupby(['subject_id'])['no_value_emotion']
    df['no_value_emotion_proportion'] = group.transform(lambda x: round(sum(x) / len(x) * 100, 1))

    # drop those subjects with proportion of missing data greater then a given threshold
    df_i = df[['video_id', 'subject_id']].drop_duplicates()
    df = df.drop(df[df['no_value_emotion_proportion'] > threshold].index)
    df_f = df[['video_id', 'subject_id']].drop_duplicates()

    # compute proportion of removed subjects: for each video and total
    x = pd.DataFrame({'before': pd.Series(df_i['video_id'].value_counts()),
                      'after': pd.Series(df_f['video_id'].value_counts())})
    x['removed'] = round((x.before - x.after) / x.before * 100, 1)
    x['removed_total'] = round((x.before.sum() - x.after.sum()) / x.before.sum() * 100, 1)

    print('Video ID \t Proportion of removed subjects per each video, in %')
    print(x['removed'])
    print('In total it was removed {}% of subjects \n'.format(x['removed_total'].tolist()[0]))

    return df


def plot_num_of_frames(df_input, bins=(100, 50)):

    """
    Plots distribution of number of frames: for each video and for all videos

    @param df_input: an input dataframe
    @param bins: a tuple (a,b): a and b correspond to number of bins in hist plot; a - all videos, b - video i
    """

    df = df_input.copy()
    df = df[['video_id', 'subject_id', 'no_of_frames']]
    df.drop_duplicates(inplace=True)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 11))
    fig.suptitle("Number of frames distribution", fontsize=20)

    # all videos distribution
    x = df[['no_of_frames']].copy()
    ax1.hist(x, bins=bins[0], edgecolor="k")
    ax1.set_title('all videos')

    # per video
    y = df[['video_id', 'no_of_frames']].copy()
    ids = set(y['video_id'])
    for id, ax in zip(ids, [ax2, ax3, ax4]):
        x = y[y['video_id'] == id]['no_of_frames'].copy()
        ax.hist(x, bins=bins[1], edgecolor="k")
        ax.set_title('Video ID: {}'.format(id))


def plot_time(df_input, bins=100):

    """
    Plots time distribution for each video

    @param df_input: an input dataframe
    @param bins: int; number of bins in hist plot
    """

    df = df_input.copy()
    df = df[['video_id', 'millisecond_from_start']]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))
    fig.suptitle("Time distribution", fontsize=20)

    # per video
    y = df[['video_id', 'millisecond_from_start']].copy()
    ids = set(y['video_id'])
    for id, ax in zip(ids, [ax1, ax2, ax3]):
        x = y[y['video_id'] == id]['millisecond_from_start'].copy()
        ax.hist(x, bins=bins, edgecolor="k")
        ax.set_title('Video ID: {}'.format(id))


def plot_emotion_evolution(df_input, metrics=None, compare=None):

    """
    Plots time evolution of emotions for each video

    @param df_input: an input dataframe
    @param metrics: column names in df_input corresponding to computed metrics
    @param compare: None, 'videos', 'metrics'; None - plots emotion evolution for each video and chosen metrics,
                    'videos' - to compare videos, 'metrics' - to compare metrics
    """

    if metrics is None:
        metrics = metrics_avg

    df = df_input.copy()
    df.rename(columns={'time_bin': 'Time, ms'}, inplace=True)
    df.set_index('Time, ms', inplace=True)
    ids = set(df['video_id'])

    # Plot emotions evolution (different metrics) for each video
    if compare == None:

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))
        fig.suptitle("Emotions evolution", fontsize=20)

        for id, ax in zip(ids, [ax1, ax2, ax3]):
            x = df[df['video_id'] == id].copy()
            x[metrics].plot(ax=ax)
            ax.set_title('Video ID: {}'.format(id))
            ax.axhline(y=0, color='r', linestyle='-')

    # Compare videos
    if compare == 'videos':

        # plot
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))
        fig.suptitle("Emotions evolution. Videos comparison.", fontsize=20)

        for m, ax in zip(metrics, [ax1, ax2, ax3]):
            df.groupby('video_id')[m].plot(legend=True, ax=ax, kind='line')
            ax.set_title(m)
            ax.axhline(y=0, color='r', linestyle='-')

    # Compare metrics
    if compare == 'metrics':

        # shift metrics to zero
        metrics_centered = [m + '_centered' for m in metrics]
        for m in metrics:
            df[m + '_centered'] = df.groupby('video_id')[m].apply(lambda x: x - x.mean())

        # compute difference between metrics
        df['delta_12'] = df[metrics[0] + '_centered'] - df[metrics[1] + '_centered']
        df['delta_13'] = df[metrics[0] + '_centered'] - df[metrics[2] + '_centered']

        # plot centered metrics and metrics differences
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(20, 10))
        fig.suptitle("Emotions evolution. Centered metrics & metrics difference.", fontsize=20)

        for id, ax in zip(ids, [ax1, ax2, ax3]):
            x = df[df['video_id'] == id].copy()
            x[metrics_centered].plot(ax=ax)
            ax.axhline(y=0, color='r', linestyle='-')
            ax.set_title('Video ID: {}'.format(id))

        for id, ax in zip(ids, [ax4, ax5, ax6]):
            x = df[df['video_id'] == id].copy()
            x[['delta_12', 'delta_13']].plot(ax=ax)
            ax.axhline(y=0, color='r', linestyle='-')