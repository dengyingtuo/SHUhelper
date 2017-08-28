import datetime

from mongoengine import (DateTimeField, IntField,
                         ListField, ReferenceField, StringField)
from flask_login import current_user
from UHE.extensions import db
# from config import db
from UHE.user.models import User


class Feed(db.Document):
    user = ReferenceField(User)
    created = DateTimeField(default=datetime.datetime.now)
    comments = IntField(default=0)
    feed_type = StringField()  # external-link internal-link imgs text post
    text = StringField(default='')
    link_URL = StringField()
    link_title = StringField()
    link_img = StringField()
    img = ListField(StringField())
    like = ListField(ReferenceField(User, deref=True), default=lambda: [])
    meta = {
        'ordering': ['-created'],
        'strict': False
    }

    def __unicode__(self):
        return self.text

    def to_dict(self):
        # print(current_user.id,list(map(lambda user: user.id,self.like)))
        return {
            'user': self.user.to_dict_public(),
            'created': str(self.created),
            'comments': self.comments,
            'type': self.feed_type,
            'text': self.text,
            'linkURL': self.link_URL,
            'linkTitle': self.link_title,
            'linkImg': self.link_img,
            'img': self.img,
            'like': self.like,
            'id': str(self.id),
            'liked': current_user.id in list(map(lambda user: user.id, self.like)),
            'likecount': len(self.like)
        }