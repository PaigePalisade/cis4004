from sqlalchemy import Integer, String
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    body: Mapped[str]
    room: Mapped[str]
    timestamp: Mapped[int]

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    password: Mapped[str]

class Room(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

class ExternalMessage(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    display_name: Mapped[str]
    pfp: Mapped[str]
    body: Mapped[str]
    room: Mapped[str]
    timestamp: Mapped[int]

class Bridge(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    internal_channel: Mapped[str]
    external_channel: Mapped[str]
    webhook: Mapped[str]