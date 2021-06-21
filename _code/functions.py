"""
    Here we collect all the necessary functions
"""

import pandas as pd
import os


def data_path(i):

    """ Returns path to video data """

    HOME = os.getcwd()
    return HOME + '/_data/realeyes_dsc_homework_video_{}.csv'.format(i)


def remove_duplicates(df):

    """ Removes duplicates """

    columns = ['video_id', 'subject_id', 'frame_no', 'millisecond_from_start',
               'positive_1', 'positive_2', 'negative_1', 'negative_2', 'negative_3']
    size_i = df.shape[0]
    df.drop_duplicates(columns, inplace=True)
    size_f = df.shape[0]
    print(size_i - size_f, 'duplicates dropped')

    return df


def load_data(path):

    """ Loads video data """

    df1 = pd.read_csv(path(1))
    df2 = pd.read_csv(path(2))
    df3 = pd.read_csv(path(3))
    for df in [df1, df2, df3]:
        df = remove_duplicates(df)

    df = pd.concat([df1, df2, df3], ignore_index=True)

    # df = df.sort_values(by=['video_id', 'subject_id', 'frame_no', 'millisecond_from_start'], ignore_index=True)

    return df, df1, df2, df3


def no_value(df):

    """ Shows non-numeric values and its count """

    for column in columns:
        idx = pd.to_numeric(df[column], errors='coerce').isna()
        no_val = list(set(df[idx][column]))
        no_val_len = len(df[idx][column])
        print(no_val, "{}%".format(round(no_val_len / df.shape[0] * 100)))


def replace_no_value_sub(df, method='preceding'):

    """ Replaces 'No value' in video_id & subject_id by the preceding value"""

    for c in ['video_id', 'subject_id']:
        df[c] = pd.to_numeric(df[c], errors='coerce', downcast='integer')
        if method == 'preceding':
            df[c].fillna(method='ffill', inplace=True)
        if method == 'following':
            df[c].fillna(method='bfill', inplace=True)
        df[c] = df[c].astype('int32').astype('str')

    return df


def replace_no_value(df_input):

    """
        Replace 'No value' entries by preceding/following value if the 'frame_no' changes by 1 with respect to
        previous/next value.
    """

    df = df_input.copy()

    # label missing entries
    df['no_value_id'] = df['subject_id'].apply(lambda x: 1 if str(x) == 'No value' else 0)
    df['no_value'] = df['no_value_id']

    # restrict data frame to missing + neighbour values
    df = df[(df['no_value'] == 1) | (df['no_value'].shift() == 1) | (df['no_value'].shift(-1) == 1)]

    # count consequent missing entries: [0,0,1,0,1,1,0,0] will correspond to [0,0,1,0,2,2,0,0]
    group = df.groupby((df['no_value'] != df['no_value'].shift()).cumsum())
    df['no_value_count'] = group['no_value'].transform('sum')

    # replace missing values by preceding value
    df = replace_no_value_sub(df, 'preceding')

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
    df = replace_no_value_sub(df, 'following')

    # compute difference between current and following value for 'frame_no'
    df['frame_no_diff'] = df.groupby(['subject_id'])['frame_no'].transform(lambda x: x.diff().abs().shift(-1))

    # if frame number did not change by 1, change back to 'No value'
    for c in ['video_id', 'subject_id']:
        df.loc[(df['frame_no_diff'] != 1) & (df['no_value'] == 1), c] = 'No value'

    if set(df[df.no_value==1]['frame_no_diff']) == {1}:
        print('All id missing values were successfully replaced')
    else:
        print('Not all missing values were replaced. Investigate manually!')

    return df[df.columns[:-3]]

