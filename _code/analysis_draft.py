"""

"""


from _code.functions import *


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
plot_emotion_evolution(df_emotion, metrics=metrics_avg, compare='metrics')
plot_emotion_evolution(df_emotion, metrics=metrics_avg, compare='videos')

