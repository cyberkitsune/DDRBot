from peewee import *
import datetime

db = SqliteDatabase('score_db.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = IntegerField(primary_key=True)
    display_name = TextField()


class Score(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref='scores')
    song_title = TextField()
    song_artist = TextField()
    difficulty_number = IntegerField()
    difficulty_name = TextField()
    letter_grade = TextField()
    full_combo = TextField()
    doubles_play = BooleanField()
    money_score = IntegerField()
    ex_score = IntegerField()
    marv_count = IntegerField()
    perf_count = IntegerField()
    great_count = IntegerField()
    good_count = IntegerField()
    OK_count = IntegerField()
    miss_count = IntegerField()
    max_combo = IntegerField()
    recorded_time = DateTimeField(default=datetime.datetime.now)
    file_name = TextField()
