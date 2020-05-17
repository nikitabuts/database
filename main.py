from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_filters import apply_filters
from flask_marshmallow import Marshmallow
from flask import Flask
from flask import Flask, jsonify, request
from sqlalchemy.sql import func
from flask_cors import CORS




class Pair:

    def __init__(self, db, tables, ops):
        self.db = db
        self.tables = tables
        self.ops = ops

    def public_subscribers(self, user_id, public_id):
        user = self.ops.return_row("user", id=user_id)
        public = self.ops.return_row("public", id=public_id)

        if user is None:
            raise ValueError('Пользователя с таким id не существует!')

        if public is None:
            raise ValueError('Паблика с таким id не существует!')


        public.subscribers.append(user)
        self.db.session.commit()

        return True

    def user_post_published(self, user_id, post_id):
        user = self.ops.return_row("user", id=user_id)
        post = self.ops.return_row("post", id=post_id)

        if user is None:
            raise ValueError('Пользователя с таким id не существует!')

        if post is None:
            raise ValueError('Поста с таким id не существует!')

        post.published.append(user)
        self.db.session.commit()

        return True

    def public_post_published(self, post_id, public_id):

        post = self.ops.return_row("post", id=post_id)
        public = self.ops.return_row("public", id=public_id)

        if post is None:
            raise ValueError('Поста с таким id не существует!')

        if public is None:
            raise ValueError('Паблика с таким id не существует!')

        post.pub_published.append(public)
        self.db.session.commit()

        return True

    def user_chat_member(self, user_id, chat_id):

        user = self.ops.return_row("user", id=user_id)
        chat = self.ops.return_row("chat", id=chat_id)

        if user is None:
            raise ValueError('Пользователя с таким id не существует!')

        if chat is None:
            raise ValueError('Чата с таким id не существует!')


        chat.chat_join.append(user)
        self.db.session.commit()

        return True

    def user2message(self, user_id, message_text):

        user = self.ops.return_row("users", id=user_id)
        if user is None:
            raise ValueError('Чата с таким id не существует!')
        message = self.db.Message(text=message_text, sentby=user)

        self.db.session.add(message)
        self.db.session.commit()

        return True

    def chat2message(self, chat_id, message_text):

        chat = Operations.return_row("chat", id=chat_id)
        if chat is None:
            raise ValueError('Чата с таким id не существует!')

        message = self.db.Message(text=message_text,
                          chat=chat)

        self.db.session.add(message)
        self.db.session.commit()

        return True



class Operations:
    db = None
    tables = None

    def return_row(self, ClassName, id):
        return self.tables[ClassName].query.filter_by(id=id).first()

    def return_table(self, ClassName):
        return self.tables[ClassName].query.all()

        # Пример:
        # for el in return_table(Users):
        #   print(el.u_nick)

    def appending(self, ClassName, *args):
        try:
            element = self.tables[ClassName](*args)
        except TypeError:
            raise ("Wrong number of table parameters")
        else:
            self.db.session.add(element)
            self.db.session.commit()
            return True

    def remove(self, ClassName, id):  # удаление нашел только по id (оно почему-то не удаляет :( )
        try:
            delete = self.tables[ClassName].query.filter_by(id=id).first()
        except ValueError:
            raise ValueError('Либо такого id нет в базе, либо нет такого класса')
        else:
            self.db.session.delete(delete)
            self.db.session.commit()
            return True

    def update(self, ClassName, id, column_name, value):
        try:
            update = self.tables[ClassName].query.filter_by(id=id).first()
        except ValueError:
            raise ValueError('Либо такого id нет в базе, либо нет такого класса')
        else:
            setattr(update, column_name,
                    value)  # ClassName object is not subscripitable (можно обращаться к update только через точку,
            # а не через [])
            self.db.session.commit()
            return True

    @staticmethod
    def erase(ClassName):
        table = Operations.return_table(ClassName)
        for row in table:
            Operations.remove(ClassName, row.id)
        return True

    def filter(self, ClassName, column, value, operation='=='):  # operation может быть не только '==', но и '<', '>'
        query = self.db.session.query(self.tables[ClassName])
        filter_spec = [{'field': column, 'op': operation, 'value': value}]
        result = apply_filters(query, filter_spec).all()
        return result

    def __init__(self, database, table):
        self.db = database
        self.tables = table


class Context:
    def create_db(self):
        self.db.create_all()

    def __init__(self, application):
        self.app = application
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{user}:{pw}@{url}/{db}'.format(user='postgres',
                                                                                                  pw='2423',
                                                                                                  url='dvv2423.fvds.ru',
                                                                                                  db='social_network')
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

        self.db = SQLAlchemy(self.app)

        self.ma = Marshmallow(self.app)

        self.public_subscribers = self.db.Table('PublicSubscribers',  # работает без ролей
                                                self.db.Column('pub_id', self.db.Integer,
                                                               self.db.ForeignKey('public.id')),
                                                self.db.Column('u_id', self.db.Integer, self.db.ForeignKey('users.id')),
                                                self.db.Column('ps_role', self.db.Integer,
                                                               self.db.ForeignKey('roles.id'))
                                                )

        self.post_published_by_user = self.db.Table('PostPublisheself.dbyUser',  # работает
                                                    self.db.Column('pub_id', self.db.Integer,
                                                                   self.db.ForeignKey('post.id')),
                                                    self.db.Column('pu_id', self.db.Integer,
                                                                   self.db.ForeignKey('users.id'))
                                                    )

        self.post_published_by_public = self.db.Table('PostPublisheself.dbyPublic',  # работает
                                                      self.db.Column('pub_id', self.db.Integer,
                                                                     self.db.ForeignKey('post.id')),
                                                      self.db.Column('pu_id', self.db.Integer,
                                                                     self.db.ForeignKey('public.id'))
                                                      )

        self.chat_members = self.db.Table('ChatMembers',  # работает без ролей
                                          self.db.Column('chat', self.db.Integer, self.db.ForeignKey('chat.id')),
                                          self.db.Column('member', self.db.Integer, self.db.ForeignKey('users.id')),
                                          self.db.Column('role', self.db.Integer,
                                                         self.db.ForeignKey('roles.id'))
                                          )

        class Friendship(self.db.Model):
            __tablename__ = 'Friendship'
            subscriber_id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.id'), primary_key=True)

            def __init__(self, s_id, u_id):
                self.subscriber_id = s_id
                self.user_id = u_id

        class FriendshipSchema(self.ma.Schema):
            class Meta:
                fields = ('subscriber_id', 'user_id')

        self.friendship = Friendship
        self.friendship_schema = FriendshipSchema()
        self.friendships_schema = FriendshipSchema(many=True)

        class Users(self.db.Model):
            id = self.db.Column(self.db.INTEGER, primary_key=True)
            nick = self.db.Column(self.db.VARCHAR(50), nullable=False)
            avatar = self.db.Column(self.db.VARCHAR(200))
            descr = self.db.Column(self.db.VARCHAR(500))
            password = self.db.Column(self.db.VARCHAR(50), nullable=False)
            name = self.db.Column(self.db.VARCHAR(50))
            surname = self.db.Column(self.db.VARCHAR(50))

            user_subscribers = self.db.relationship('Friendship')

            subscriptions = self.db.relationship('Public', secondary=self.public_subscribers,
                                                 backref=self.db.backref('subscribers', lazy='dynamic'))

            user_post_published = self.db.relationship('Post', secondary=self.post_published_by_user,
                                                       backref=self.db.backref('published', lazy='dynamic'))

            user_chat_member = self.db.relationship('Chat', secondary=self.chat_members,
                                                    backref=self.db.backref('chat_join', lazy='dynamic'))

            user_messages = self.db.relationship('Message', backref='user_message_owner')

            def __init__(self, nick, avatar,
                         descr, password, name,
                         surname):
                self.nick = nick
                self.avatar = avatar
                self.descr = descr
                self.password = password
                self.name = name
                self.surname = surname

        class UserSchema(self.ma.Schema):
            class Meta:
                fields = ('id', 'nick', 'avatar', 'descr', 'password', 'name', 'surname')

        self.user = Users
        self.user_schema = UserSchema()
        self.users_schema = UserSchema(many=True)

        class Message(self.db.Model):
            id = self.db.Column(self.db.INTEGER, primary_key=True)
            time = self.db.Column(self.db.DATE, default=func.now(), nullable=False)
            text = self.db.Column(self.db.VARCHAR(1000), nullable=False)
            sentby = self.db.Column(self.db.Integer, self.db.ForeignKey('users.id'))
            chat = self.db.Column(self.db.Integer, self.db.ForeignKey('chat.id'))

            def __init__(self, text, time, sentby, chat):
                self.text = text
                self.time = time
                self.sentby = sentby
                self.chat = chat

        class MessageSchema(self.ma.Schema):
            class Meta:
                fields = ('id', 'time', 'text', 'sentby', 'chat')

        self.message = Message
        self.message_schema = MessageSchema()
        self.messages_schema = MessageSchema(many=True)

        class Chat(self.db.Model):
            id = self.db.Column(self.db.INTEGER, primary_key=True)
            type = self.db.Column(self.db.VARCHAR(12), nullable=False)
            title = self.db.Column(self.db.VARCHAR(80), nullable=False)
            avatar = self.db.Column(self.db.VARCHAR(100))

            chat_messages = self.db.relationship('Message', backref='chat_message_owner')

            def __init__(self, type, title,
                         avatar=None):
                self.type = type
                self.title = title
                self.avatar = avatar

        class ChatSchema(self.ma.Schema):
            class Meta:
                fields = ('id', 'type', 'title', 'avatar', 'count', 'members')

        self.chat = Chat
        self.chat_schema = ChatSchema()
        self.chats_schema = ChatSchema(many=True)

        class Post(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            text = self.db.Column(self.db.VARCHAR(1000), nullable=False)
            photo = self.db.Column(self.db.VARCHAR(200))
            time = self.db.Column(self.db.DATE, default=func.now())
            views = self.db.Column(self.db.NUMERIC(7), default=0, nullable=False)
            likes = self.db.Column(self.db.NUMERIC(7), default=0, nullable=False)

            def __init__(self, text, time=func.now(), photo=None,
                         views=0, likes=0):
                self.text = text
                self.time = time
                self.photo = photo
                self.views = views
                self.likes = likes

        class PostSchema(self.ma.Schema):
            class Meta:
                fields = ('text', 'time', 'photo', 'views', 'likes')

        self.post = Post
        self.post_schema = PostSchema()
        self.posts_schema = PostSchema(many=True)

        class Public(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            title = self.db.Column(self.db.VARCHAR(80), nullable=False)
            avatar = self.db.Column(self.db.VARCHAR(100))
            description = self.db.Column(self.db.VARCHAR(200))
            post_published = self.db.relationship('Post', secondary=self.post_published_by_public,
                                                  backref=self.db.backref('pub_published', lazy='dynamic'))

            def __init__(self, title, description=None, avatar=None):
                self.title = title
                self.description = description
                self.avatar = avatar

        class PublicSchema(self.ma.Schema):
            class Meta:
                fields = ('id', 'title', 'avatar', 'description')

        self.public = Public
        self.public_schema = PublicSchema()
        self.publics_schema = PublicSchema(many=True)

        class Roles(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            title = self.db.Column(self.db.VARCHAR(30), nullable=False)

            def __init__(self, title):
                self.title = title

        class RolesSchema(self.ma.Schema):
            class Meta:
                fields = ('id', 'title')

        self.roles = Roles
        self.role_schema = RolesSchema()
        self.roles_schema = RolesSchema(many=True)

        self.tables = {'user': Users,
                       'message': Message,
                       'chat': Chat,
                       'post': Post,
                       'friendship': Friendship,
                       'public': Public,
                       'role': Roles}

        self.ops = Operations(self.db, self.tables)
        self.check = Pair(self.db, self.tables, ops=self.ops)



def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'mysupersecretkey'
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    context = Context(app)
    context.create_db()

    context.check.public_subscribers(user_id=3, public_id=2)



