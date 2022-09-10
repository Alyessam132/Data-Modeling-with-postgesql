import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    # open song file
    df = pd.read_json(filepath, lines=True)
    song_data = df[['song_id','title','artist_id','year', 'duration']]
    artist_data = df[['artist_id','artist_name', 'artist_location', 'artist_longitude', 'artist_latitude']]
    # insert song record
    for i, row in song_data.iterrows():
        cur.execute(song_table_insert, row)
    
    # insert artist record
    for i, row in artist_data.iterrows():
        cur.execute(artist_table_insert, row)


def process_log_file(cur, filepath):
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[df['page'] == 'NextSong']

    # convert timestamp column to datetime
    df.ts = t = pd.to_datetime(df.ts, unit = 'ms')
    
    # insert time data records
    hour = pd.Series(t.dt.hour, name = 'hour')
    day = pd.Series(t.dt.day, name = 'day')
    week = pd.Series(t.dt.week, name = 'week')
    month = pd.Series(t.dt.month, name = 'month')
    year =  pd.Series(t.dt.year, name = 'year')
    day_name = pd.Series(t.dt.day_name(), name = 'weekday')
    time_df = pd.concat([t,hour,day,week,month,year,day_name],axis =1)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId','firstName','lastName','gender','level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (index, row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent )
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()