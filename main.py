from sqlalchemy.sql import func
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_filters import apply_filters


def db_connection(user, password, psql_url, psql_db):                                       #Индивидуально для каждого
    db_url = 'postgresql://{user}:{pw}@{url}/{db}'.format(user=user, pw=password,           #Пример: postgresql://scott:tiger@localhost/mydatabase
                                                          url=psql_url, db=psql_db)         # (база данных уже должна быть создана)
    return db_url                                                                           # (У меня Ubuntu, для Винды может быть другой способ подключения)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_connection(user='postgres', password='2423',
                                                      psql_url='dvv2423.fvds.ru', psql_db='social_network_2')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False           # silence the deprecation warning

db = SQLAlchemy(app)


public_subscribers = db.Table('PublicSubscribers',                    #работает без ролей
    db.Column('pub_id', db.Integer, db.ForeignKey('public.id')),
    db.Column('u_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('ps_role', db.Integer, db.ForeignKey('roles.id'))
)

post_published_by_user = db.Table('PostPublishedByUser',                  #работает
    db.Column('pub_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('pu_id', db.Integer, db.ForeignKey('users.id'))
)

post_published_by_public = db.Table('PostPublishedByPublic',                  #работает
    db.Column('pub_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('pu_id', db.Integer, db.ForeignKey('public.id'))
)

chat_members = db.Table('ChatMembers',                                      #работает без ролей
    db.Column('chat', db.Integer, db.ForeignKey('chat.id')),
    db.Column('member', db.Integer, db.ForeignKey('users.id'))
)

#friends = db.Table('Friends',                                          не работает
#    db.Column('id_1', db.Integer, db.ForeignKey('users.id')),
#    db.Column('id_2', db.Integer, db.ForeignKey('users.id'))
#)


class Users(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    nick = db.Column(db.VARCHAR(50), nullable=False)
    avatar = db.Column(db.VARCHAR(200))
    descr = db.Column(db.VARCHAR(500))
    password = db.Column(db.VARCHAR(50), nullable=False)
    name = db.Column(db.VARCHAR(50))
    surname = db.Column(db.VARCHAR(50))

    subscriptions = db.relationship('Public', secondary=public_subscribers,
                                    backref=db.backref('subscribers', lazy='dynamic'))

    user_post_published = db.relationship('Post', secondary=post_published_by_user,
                                          backref=db.backref('published', lazy='dynamic'))

    user_chat_member = db.relationship('Chat', secondary=chat_members,
                                       backref=db.backref('chat_join', lazy='dynamic'))

    user_messages = db.relationship('Message', backref='user')

    #followers = db.relationship('Users', secondary=friends,
     #                           backref=db.backref('subscribe', lazy='dynamic'))

    def __init__(self, nick, avatar,
                 descr, password, name,
                 surname):

        self.nick = nick
        self.avatar = avatar
        self.descr = descr
        self.password = password
        self.name = name
        self.surname = surname


class Message(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    time = db.Column(db.DATE, default=func.now(), nullable=False)
    text = db.Column(db.VARCHAR(1000), nullable=False)
    sentby = db.Column(db.Integer, db.ForeignKey('users.id'))
    chat = db.Column(db.Integer, db.ForeignKey('chat.id'))

    def __init__(self, text, time=func.now(), sentby=None, chat=None):
        self.text=text
        self.time=time
        self.sentby = sentby
        self.chat = chat


class Chat(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    type = db.Column(db.VARCHAR(12), nullable=False)
    title = db.Column(db.VARCHAR(80), nullable=False)
    avatar = db.Column(db.VARCHAR(100))

    chat_messages = db.relationship('Message', backref='chat')

    def __init__(self, type, title,
                 avatar=None):
        self.type=type
        self.title=title
        self.avatar=avatar


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.VARCHAR(1000), nullable=False)
    photo = db.Column(db.VARCHAR(200))
    time = db.Column(db.DATE, default=func.now())
    views = db.Column(db.NUMERIC(7), default=0, nullable=False)
    likes = db.Column(db.NUMERIC(7), default=0, nullable=False)

    def __init__(self, text, time=func.now(), photo=None,
                 views=0, likes=0):
        self.text = text
        self.time=time
        self.photo=photo
        self.views=views
        self.likes=likes


class Public(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.VARCHAR(80), nullable=False)
    avatar = db.Column(db.VARCHAR(100))
    description = db.Column(db.VARCHAR(200))
    post_published = db.relationship('Post', secondary=post_published_by_public,
                                            backref=db.backref('pub_published', lazy='dynamic'))

    def __init__(self, title, description=None, avatar=None):
        self.title = title
        self.description = description
        self.avatar = avatar


class Roles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.VARCHAR(30), nullable=False)

    def __init__(self, title):
        self.title=title


class Pair:
    @staticmethod
    def public_subscribers(user_id, public_id):
        user = Operations.return_row("users", id=user_id)
        public = Operations.return_row("public", id=public_id)

        if user is None:
            raise ValueError('Пользователя с таким id не существует!')

        if public is None:
            raise ValueError('Паблика с таким id не существует!')


        public.subscribers.append(user)
        db.session.commit()

        return True


    @staticmethod
    def user_post_published(user_id, post_id):
        user = Operations.return_row("users", id=user_id)
        post = Operations.return_row("post", id=post_id)

        if user is None:
            raise ValueError('Пользователя с таким id не существует!')

        if post is None:
            raise ValueError('Поста с таким id не существует!')

        post.published.append(user)
        db.session.commit()

        return True

    @staticmethod
    def public_post_published(post_id, public_id):

        post = Operations.return_row("post", id=post_id)
        public = Operations.return_row("public", id=public_id)

        if post is None:
            raise ValueError('Поста с таким id не существует!')

        if public is None:
            raise ValueError('Паблика с таким id не существует!')

        post.pub_published.append(public)
        db.session.commit()

        return True

    @staticmethod
    def user_chat_member(user_id, chat_id):

        user = Operations.return_row("users", id=user_id)
        chat = Operations.return_row("chat", id=chat_id)

        if user is None:
            raise ValueError('Пользователя с таким id не существует!')

        if chat is None:
            raise ValueError('Чата с таким id не существует!')


        chat.chat_join.append(user)
        db.session.commit()

        return True

    @staticmethod
    def user2message(user_id, message_text):

        user = Operations.return_row("users", id=user_id)
        if user is None:
            raise ValueError('Чата с таким id не существует!')
        message = Message(text=message_text, sentby=user)

        db.session.add(message)
        db.session.commit()

        return True

    @staticmethod
    def chat2message(chat_id, message_text):

        chat = Operations.return_row("chat", id=chat_id)
        if chat is None:
            raise ValueError('Чата с таким id не существует!')

        message = Message(text=message_text,
                          chat=chat)

        db.session.add(message)
        db.session.commit()

        return True



    #def friends_checking():
    #   user1 = Users(nick='VasilyPupkin', avatar='rqwqq', descr='Vasily', password=1225,
    #                 name='Vasily', surname='Pupkin')
    #   user2 = Users(nick='DonaldTrump', avatar='rqdwwqq', descr='America', password=1225,
    #                 name='Hi', surname='Clinton')

    #    db.session.add(user1)
    #   db.session.add(user2)
    #  user1.subscribe.append(user2)
    #  db.session.commit()


tables = {'users': Users,
          'message': Message,
          'chat': Chat,
          'post': Post,
          'public': Public,
          'roles': Roles}


class Operations:

    def __init__(self):
        pass

    @staticmethod
    def return_row(ClassName, id):
        return tables[ClassName].query.filter_by(id=id).first()

    @classmethod
    def return_table(self, ClassName):
        return tables[ClassName].query.all()

        #Пример:
        #for el in return_table(Users):
        #   print(el.u_nick)

    @staticmethod
    def appending(ClassName, *args):
        try:
            element = tables[ClassName](*args)
        except TypeError:
            raise("Wrong number of table parameters")
        else:
            db.session.add(element)
            db.session.commit()
            return True


    @classmethod
    def remove(self, ClassName, id):      #удаление нашел только по id (оно почему-то не удаляет :( )
        try:
            delete = tables[ClassName].query.filter_by(id=id).first()
        except ValueError:
            raise ValueError('Либо такого id нет в базе, либо нет такого класса')
        else:
            db.session.delete(delete)
            db.session.commit()
            return True

    @staticmethod                                           #не работает
    def update(ClassName, id, column_name, value):
        try:
            update = tables[ClassName].query.filter_by(id=id).first()
        except ValueError:
            raise ValueError('Либо такого id нет в базе, либо нет такого класса')
        else:
            setattr(update, column_name, value)               #ClassName object is not subscripitable (можно обращаться к update только через точку, а не через [])
            db.session.commit()
            return True

    @staticmethod
    def erase(ClassName):
        table = Operations.return_table(ClassName)
        for row in table:
            Operations.remove(ClassName, row.id)
        return True

    @staticmethod
    def filter(ClassName, column, value, operation='=='):       #operation может быть не только '==', но и '<', '>'
        query = db.session.query(tables[ClassName])
        filter_spec = [{'field': column, 'op': operation, 'value': value}]
        result = apply_filters(query, filter_spec).all()
        return result


def main():  #Кто опять будет тупить и не запустит эту функцию перед запуском скрипта - тот здохнед
    db.create_all()



    Pair.public_subscribers(user_id=14, public_id=2)




