from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean

class DDRScoreDB(object):

    def __init__(self):
        self.engine = create_engine("sqlite://ddr_score.db")
        self.meta = MetaData()

        self.scores = Table(
            'scores', self.meta,
            Column('id', Integer, primary_key=True),
            Column('song_name', String),
            Column('song_artist', String),
            Column('song_difficulty', String),
            Column('letter_grade', String),
            Column('money_score', String),
            Column('ex_score', String),
            Column('doubles', Boolean),
            Column('marv', Integer),
            Column('perfect', Integer),
            Column('great', Integer),
            Column('good', Integer),
            Column('OK', Integer),
            Column('miss', Integer),


        )

        self.users = Table(
            'users', self.meta,
            Column('id', Integer, primary_key=True),
            Column('display_name', String),
        )

        self.meta.create_all(self.engine)
