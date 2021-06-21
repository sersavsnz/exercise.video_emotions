'''
    Clean the code:
        - function description: provide a detailed description, comments and list parameters
        -

    To do:
        - replace missing ids
        - remove missing emotions: 1. subjects with too many missing values 2. missing values
        - statistics on removed data
        - statistics:
          1. subjects per video
          2.
'''

import pandas as pd
import os
import matplotlib.pyplot as plt


def data_path(i):

    """ Returns path to video data """

    HOME = os.getcwd()
    return HOME + '/_data/realeyes_dsc_homework_video_{}.csv'.format(i)


def remove_duplicates(df_input):

    """ Removes duplicates """

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

    """ Loads video data """

    print('Load data')

    df1 = pd.read_csv(path(1))
    df2 = pd.read_csv(path(2))
    df3 = pd.read_csv(path(3))
    for df in [df1, df2, df3]:
        df = remove_duplicates(df)

    df = pd.concat([df1, df2, df3], ignore_index=True)

    print('Data loaded \n')

    return df, df1, df2, df3


def no_value(df):

    """ Shows non-numeric values and its count """

    for column in columns:
        idx = pd.to_numeric(df[column], errors='coerce').isna()
        no_val = list(set(df[idx][column]))
        no_val_len = len(df[idx][column])
        print(no_val, "{}%".format(round(no_val_len / df.shape[0] * 100)))


def replace_no_value_id_sub(df, method='preceding'):

    """ Replaces 'No value' in video_id & subject_id by the preceding value"""

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
    """

    df = df_input.copy()

    # label missing entries
    df['no_value'] = df['no_value_id']

    # restrict data frame to missing + neighbour values
    df = df[(df['no_value'] == 1) | (df['no_value'].shift() == 1) | (df['no_value'].shift(-1) == 1)]

    # count consequent missing entries: [0,0,1,0,1,1,0,0] will correspond to [0,0,1,0,2,2,0,0]
    group = df.groupby((df['no_value'] != df['no_value'].shift()).cumsum())
    df['no_value_count'] = group['no_value'].transform('sum')

    # replace missing values by preceding value
    df = replace_no_value_id_sub(df, 'preceding')

    # compute difference between current and previous value for 'frame_no'
    df['frame_no_diff'] = df.groupby(['subject_id'])['frame_no'].transform(lambda x: x.diff().abs())

    # if one of (frame_no_diff != 1) in a group of consequent missing values => label all in a group with this value
    group = df.groupby((df['no_value'] != df['no_value'].shift()).cumsum())
    df['frame_no_diff'] = group['frame_no_diff'].transform('max')

    # if frame number did not change by 1, change back to 'No value'
    for c in ['video_id', 'subject_id']:
        df.loc[(df['frame_no_diff'] != 1) & (df['no_value'] == 1), c] = 'No value'

    # label missing entries
    df['no_value'] = df['subject_id'].apply(lambda x: 1 if str(x) == 'No value' else 0)

    # replace missing values by following value
    df = replace_no_value_id_sub(df, 'following')

    # compute difference between current and following value for 'frame_no'
    df['frame_no_diff'] = df.groupby(['subject_id'])['frame_no'].transform(lambda x: x.diff().abs().shift(-1))

    # if frame number did not change by 1, change back to 'No value'
    for c in ['video_id', 'subject_id']:
        df.loc[(df['frame_no_diff'] != 1) & (df['no_value'] == 1), c] = 'No value'

    if set(df[df.no_value==1]['frame_no_diff']) == {1}:
        print('All id missing values were successfully replaced \n')
    else:
        print('Not all missing values were replaced. Investigate manually! \n')

    return df[df.columns[:-3]]


def plot_no_value_emotion(df_input):

    """
        Plots statistics on missing emotion values
    """

    df = df_input.copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14,5))
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

    """ Drops subjects with proportion of missing emotion data greater then a given threshold """

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

    """ Plots distribution of number of frames: for each video and for all videos """

    df = df_input.copy()
    df = df[['video_id', 'subject_id', 'no_of_frames']]
    df.drop_duplicates(inplace=True)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 10))
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

    """ Plots time distribution for each video """

    df = df_input.copy()
    df = df[['video_id', 'millisecond_from_start']]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 10))
    fig.suptitle("Time distribution", fontsize=20)

    # per video
    y = df[['video_id', 'millisecond_from_start']].copy()
    ids = set(y['video_id'])
    for id, ax in zip(ids, [ax1, ax2, ax3]):
        x = y[y['video_id'] == id]['millisecond_from_start'].copy()
        ax.hist(x, bins=bins, edgecolor="k")
        ax.set_title('Video ID: {}'.format(id))


# Load data
df_all, df1, df2, df3 = load_data(data_path)
columns = list(df1.columns)


# each file corresponds to only one video
print(set(df1.video_id), set(df2.video_id), set(df3.video_id))
print('')

# each subject watched only one video => can group by subject_id
print(set(df1.subject_id) & set(df2.subject_id))
print(set(df2.subject_id) & set(df3.subject_id))
print('')

# no Nan values, missing values are labeled as 'No value'.
df_all.isnull().values.any()

"""
The only non-numeric values is "No value".
Values from sets {video_id, subject_id} and {emotions} are equal to 'No value' together. For example,
if video_id = 'No value', then subject_id = 'No value' as well.

print('video 1')
no_value(df1)
print('')

print('video 2')
no_value(df2)
print('')

print('video 3')
no_value(df3)
print('')

print('video all')
no_value(df_all)
print('')

"""

# Replace missing id values
df_all['no_value_id'] = df_all['subject_id'].apply(lambda x: 1 if str(x) == 'No value' else 0)
df_all['no_value_emotion'] = df_all['positive_1'].apply(lambda x: 1 if str(x) == 'No value' else 0)
df_all.update(replace_no_value_id(df_all))


# Plot statistics on missing emotion values
plot_no_value_emotion(df_all)


# Remove missing emotion values
# remove subjects with the proportion of missing emotion data > a given threshold
df_all = remove_subjects_no_value_emotion(df_all, threshold=30)
# remove missing values
df_all = df_all.drop(df_all[df_all['no_value_emotion'] == 1].index)
df_all = df_all[columns]


# Convert to integer
for c in columns:
    df_all[c] = pd.to_numeric(df_all[c])
    df_all[c] = df_all[c].astype('int32')


# Sort and remove duplicates
df_all = df_all.sort_values(by=['video_id', 'subject_id', 'frame_no', 'millisecond_from_start'], ignore_index=True)
df_all = remove_duplicates(df_all)
print('')


# Create new features
df_all['no_of_frames'] = df_all.groupby(['subject_id'])['subject_id'].transform('size')
df_all['time_diff'] = df_all.groupby(['subject_id'])['millisecond_from_start'].transform('diff')


# Investigate the data
size = df_all.shape[0]

# Video length
print('Videos are at least 30, 53 and 46 seconds long')
print('max')
print(df_all.groupby('video_id')['millisecond_from_start'].max())
print('min')
print(df_all.groupby('video_id')['millisecond_from_start'].min())
print('')

# Sample sizes
print('Sample size:')
print('Samples are more or less statistically significant (population = 1M, Margin of error=5%, conf.level 90% = 271'
      ' / 95% = 384')
print(df_all.groupby('video_id')['subject_id'].nunique(), '\n')

# Plot Number of frames distribution
plot_num_of_frames(df_all, bins=(100, 50))

# Plot time distribution - more or less enough data
plot_time(df_all, bins=53)

# Describe time difference distribution
print('Time difference descriptive statistics:')
print(df_all['time_diff'].describe(), '\n')

# If one plots evolution of emotional response over time, then the plot would look like a cardio diagram with peaks
# corresponding to emotional response.
# We see that distribution of number of frames is very diverse: there are many subjects with small amount of frames.
# Those subjects might bring bias when calculating average emotion for each subject because of their bad coverage - when
# a time step is too big, peaks will be missed.
# However, time distribution shows that it's enough data for each of the time bin. The step is chosen to be small to
# provide a good coverage (close to continuous).
# Thus, I would propose to calculate average emotion for each bin as a first step, and then compare the plots or
# average over the beans to produce a single score.

# Count emotions
emotions = ['positive_1', 'positive_2', 'negative_1', 'negative_2', 'negative_3']
df_all['positive_count'] = df_all[emotions[:2]].sum(axis=1)
df_all['negative_count'] = df_all[emotions[-3:]].sum(axis=1)
df_all['emotions_count'] = df_all[emotions].sum(axis=1)
print('Positive emotions:')
print(round(df_all['positive_count'].value_counts().sort_index()/size*100, 1), '\n')
print('Negative emotions:')
print(round(df_all['negative_count'].value_counts().sort_index()/size*100, 1), '\n')
print('All emotions:')
print(round(df_all['emotions_count'].value_counts().sort_index()/size*100, 1), '\n')


# Split the dataset into time bins of 1 second length
bins_no = 53
df_all['time_bin'] = pd.cut(df_all['millisecond_from_start'], bins=bins_no, labels=list(range(1, bins_no+1)))


# Compute metrics
metrics = ['metric_{}'.format(i) for i in [1, 2, 3]]
df_all['metric_1'] = df_all['positive_count'] - df_all['negative_count']
df_all['metric_2'] = df_all[emotions[:2]].any(axis=1).astype(int) - \
                     (df_all[emotions[-3:]].any(axis=1)).astype(int)
df_all['metric_3'] = df_all[emotions].any(axis=1).astype(int)


# Compute average emotion for each time bin
metrics_avg = ['metric_{}_avg'.format(i) for i in [1, 2, 3]]
for i in [1, 2, 3]:
    df_all['metric_{}_avg'.format(i)] = df_all.groupby(['video_id', 'time_bin'])['metric_{}'.format(i)].transform('mean')

df_emotion = df_all[['video_id', 'time_bin']+metrics_avg].drop_duplicates()

# plot emotion evolution
plot_emotion_evolution(df_emotion, metrics=metrics_avg, compare=None)




df = df_emotion.copy()

ids = set(df['video_id'])
metrics = metrics_avg

df['delta_12'] = df[metrics[0]] - df[metrics[1]]
df['delta_13'] = df[metrics[0]] - df[metrics[2]]


fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(30, 5))
fig.suptitle("Emotions evolution", fontsize=20)

for id, ax in zip(ids, [ax1, ax2, ax3]):
    x = df[df['video_id'] == id].copy()
    x.plot(x = 'time_bin', y = metrics, ax=ax)
    ax.set_title('Video ID: {}'.format(id))
    ax.axhline(y=0, color='r', linestyle='-')




def plot_emotion_evolution(df_input, metrics, compare=None):

    """ Plots time evolution of emotions for each video """

    df = df_input.copy()

    ids = set(df['video_id'])
    num_plots = len(metrics)

    # Plot emot
    if compare == None:

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(30, 5))
        fig.suptitle("Emotions evolution", fontsize=20)

        for id, ax in zip(ids, [ax1, ax2, ax3]):
            x = df[df['video_id'] == id].copy()
            x.plot(x='time_bin', y=metrics, ax=ax)
            ax.set_title('Video ID: {}'.format(id))
            ax.axhline(y=0, color='r', linestyle='-')

    # if compare == 'metrics':
    #
    #
    # if compare == 'videos':