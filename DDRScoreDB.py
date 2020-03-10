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
    user = ForeignKeyField(User, backref='score')
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
    recorded_time = DateTimeField(default=datetime.datetime.utcnow)
    file_name = TextField()
    name_confidence = FloatField()


class IIDXScore(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref='iidxscore')
    song_title = TextField()
    song_artist = TextField()
    difficulty = TextField()
    clear_type = TextField()
    dj_grade = TextField()
    double_play = BooleanField()
    ex_score = IntegerField()
    p_great_count = IntegerField()
    great_count = IntegerField()
    good_count = IntegerField()
    bad_count = IntegerField()
    poor_count = IntegerField()
    combo_break = IntegerField()
    miss_count = IntegerField()
    fast_count = IntegerField()
    slow_count = IntegerField()
    recorded_time = DateTimeField(default=datetime.datetime.utcnow)
    file_name = TextField()
    overall_confidence = FloatField()


class DBTaskWorkItem(object):

    def __init__(self, discordID, imageFilename, imageTimestampStr, redo=False, game='ddr'):
        self.discord_id = discordID
        self.image_filename = imageFilename
        self.timestamp_string = imageTimestampStr
        self.game = game
        self.redo = redo

