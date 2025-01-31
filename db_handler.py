from sqlalchemy import create_engine, Column, Integer, String, Boolean, MetaData, Table, desc
from sqlalchemy.orm import declarative_base, sessionmaker

class DBHandler:
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=True)
        self.metadata = MetaData()


        self.memes_table = Table(
            'reddit_items',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('rank', Integer),
            Column('comments', Integer),
            Column('load_order', Integer),
            Column('url', String),
            Column('file_id', String),
            Column('signature', String),
            Column('posted_by', String),
            Column('posted_when', Integer),
            Column('checked', Boolean),
            Column('approved', Boolean),
            Column('published', Boolean),
            Column('my_comment', String)
        )

        self.stats_table = Table(
            'statistics',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('all_published_count', Integer),
            Column('all_deleted_count', Integer),
            Column('published_suggested_count', Integer),
            Column('published_manual_count', Integer),
            Column('max_rank_of_suggested', Integer),
            Column('min_rank_of_suggested', Integer),
            Column('mean_rank_of_suggested', Integer),

        )

        self.Base = declarative_base()

        class Meme(self.Base):
            __table__ = self.memes_table

        self.Meme = Meme

        class Statistics(self.Base):
            __table__ = self.stats_table

        self.Statistics = Statistics

#returns the meme with the lowest load_order
    def get_meme(self):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Query one meme from the database with filters and order by load_order in ascending order
                query = session.query(self.Meme).filter_by(checked=False, published=False).order_by(
                    self.Meme.load_order.desc())
                meme = query.first()  # Use .first() to get only one result

                return meme

            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error getting meme: {e}")

                # Rollback the transaction
                session.rollback()

# Every manually created meme has 9999 rank.So this function returns meme with the lowest id in the group of memes with 9999 ranks.
    def get_manual_meme(self):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:

                query = session.query(self.Meme).filter_by(rank=99999).order_by(
                    self.Meme.id.desc())
                meme = query.first()

                return meme
            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error getting manual meme: {e}")

                # Rollback the transaction
                session.rollback()

    def get_memes_from_queue(self):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Query the database for an unchecked, approved, and unpublished meme
                query = session.query(self.Meme).filter_by(checked=True, approved=True, published=False).order_by(
                    self.Meme.rank)
                memes = query.all()
                return memes

        except Exception as e:
            # Log an error message if an exception occurs during meme retrieval
            print(f"Error getting manual meme: {e}")

    def get_deleted_memes(self):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Query the database for deleted memes, excluding specific load_order values
                # Note: I assume load_order is a column in your Meme model
                memes = (
                    session.query(self.Meme)
                    .filter(self.Meme.checked == True, self.Meme.approved == False, self.Meme.load_order != 99999999)
                    .order_by(self.Meme.load_order.desc())
                    .all()
                )
                return memes

        except Exception as e:
            # Log an error message if an exception occurs during meme retrieval
            print(f"Error getting deleted memes: {e}")

    # return statistic for a stats menu
    def get_stat(self):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Query statistics from the database
                statistics = session.query(self.Statistics).first()

                # Check if statistics is not None before accessing attributes
                if statistics:
                    memes_toGo = session.query(self.Meme).filter_by(checked=False).count()
                    memes_in_queue = session.query(self.Meme).filter_by(checked=True, approved=True,
                                                                        published=False).count()
                    all_published_count = statistics.all_published_count
                    all_deleted_count = statistics.all_deleted_count
                    published_suggested_count = statistics.published_suggested_count
                    published_manual_count = statistics.published_manual_count
                    max_rank_of_suggested = statistics.max_rank_of_suggested
                    min_rank_of_suggested = statistics.min_rank_of_suggested
                    mean_rank_of_suggested = statistics.mean_rank_of_suggested

                    return memes_toGo, memes_in_queue, all_published_count, all_deleted_count, published_suggested_count, published_manual_count, max_rank_of_suggested, min_rank_of_suggested, mean_rank_of_suggested

            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error getting statistics: {e}")

                # Rollback the transaction
                session.rollback()

                # Return a default value or raise an exception based on your use case
                return None, None, None, None, None, None, None, None, None

# return limited statistic, which are displayed in the meme controlling menu
    def get_short_stat(self):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                memes_toGo = session.query(self.Meme).filter_by(checked=False).count()
                memes_in_queue = session.query(self.Meme).filter_by(checked=True, approved=True,published=False).count()
                return memes_toGo, memes_in_queue

            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error getting statistics: {e}")

                # Rollback the transaction
                session.rollback()

                # Return a default value or raise an exception based on your use case
                return None, None

# allows to add caption to the meme
    def set_comment(self, meme_id, value):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Retrieve the meme by ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the comment field
                    meme.my_comment = value

                    # Commit the changes to the database
                    session.commit()

            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error setting comment: {e}")

                # Rollback the transaction
                session.rollback()


# deletes caption
    def delete_comment(self, meme_id):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Retrieve the meme by ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the comment field
                    meme.my_comment = None

                    # Commit the changes to the database
                    session.commit()

            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error setting comment: {e}")

                # Rollback the transaction
                session.rollback()

    def mark_as_checked(self, meme_id, status):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Retrieve the meme by ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the checked field
                    meme.checked = status

                    # Commit the changes to the database
                    session.commit()
            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error marking meme as checked: {e}")

                # Rollback the transaction
                session.rollback()

    def mark_as_approved(self, meme_id, status):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Retrieve the meme by ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the approved field
                    meme.approved = status

                    # Commit the changes to the database
                    session.commit()
            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error marking meme as approved: {e}")

                # Rollback the transaction
                session.rollback()
    def set_highest_load_order(self, meme_id):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Retrieve the meme by ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the approved field
                    meme.load_order = 99999999

                    # Commit the changes to the database
                    session.commit()
            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error adding highest_load_order: {e}")

                # Rollback the transaction
                session.rollback()
    def mark_as_published(self, meme_id, status):
        Session = sessionmaker(bind=self.engine)

        with Session() as session:
            try:
                # Retrieve the meme by ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the approved field
                    meme.published = status

                    # Commit the changes to the database
                    session.commit()
            except Exception as e:
                # Handle exceptions (e.g., log the error)
                print(f"Error marking meme as approved: {e}")

                # Rollback the transaction
                session.rollback()

# adds 101 to the load order. So this meme will appear in 10 memes.
    def skip_meme(self, meme_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()

        try:
            # Retrieve the meme by ID
            meme = session.query(self.Meme).filter_by(id=meme_id).first()

            if meme:
                # Update the comment field
                meme.load_order -= 101

                # Commit the changes to the database
                session.commit()

        except Exception as e:
            # Handle exceptions (e.g., log the error)
            print(f"Error setting comment: {e}")
            session.rollback()

        finally:
            # Close the session
            session.close()

# this function adds new, manually created post to the db.
    def set_new_post(self, media=None, text=None):
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()

            new_post = self.Meme()

            if media is not None:
                new_post.file_id = media

            if text is not None:
                new_post.my_comment = text

            new_post.rank = 99999
            new_post.approved = False
            new_post.checked = False
            new_post.approved = False
            new_post.published = False

            session.add(new_post)
            session.commit()

            print("New post added successfully.")

        except Exception as e:
            print(f"An error occurred while adding a new post: {e}")
            session.rollback()

        finally:
            session.close()

    def modify_stat(self, symbol, **kwargs):
        Session = sessionmaker(bind=self.engine)
        session = Session()

        statistics = session.query(self.Statistics).first()

        for attr, value in kwargs.items():
            if value is not None:
                if attr == 'rank':
                    if statistics.max_rank_of_suggested < value:
                        setattr(statistics, 'mean_rank_of_suggested', (value + statistics.min_rank_of_suggested) / 2)
                        setattr(statistics, 'max_rank_of_suggested', value)
                    elif statistics.min_rank_of_suggested > value:
                        setattr(statistics, 'mean_rank_of_suggested', (value + statistics.max_rank_of_suggested) / 2)
                        setattr(statistics, 'min_rank_of_suggested', value)
                else:
                    current_value = getattr(statistics, attr, 0)
                    if symbol == '+':
                        setattr(statistics, attr, current_value + value)
                    elif symbol == '-':
                        setattr(statistics, attr, current_value - value)

        session.commit()






