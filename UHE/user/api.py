import datetime
import json

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from mongoengine.queryset.visitor import Q
from werkzeug.security import check_password_hash, generate_password_hash

from UHE.plugins.SHU_api.client import Services, Tiyu
from UHE.extensions import redis_store
from UHE.user.models import User, UserData
from UHE.utils import make_token

users = Blueprint('users', __name__)


@users.route('/query/<identifier>/', methods=['GET', 'POST'])
@login_required
def user_data(identifier):
    identifier = 'tiyu'
    if request.method == 'GET':
        user_data = UserData.objects.get_or_404(
            user=current_user.id, identifier=identifier)
        return jsonify(user_data)
    else:
        post_data = request.get_json()
        user_data = UserData.objects(
            user=current_user.id, identifier=identifier).first()
        if user_data is None:
            user_data = UserData(identifier=identifier,
                                 user=current_user.id, status='none')
            user_data.save()
        task = get_data(identifier, current_user.id,
                        post_data['password'], post_data['password'])
        return jsonify(success='ok')


def get_data(identifier, card_id, password, lock):
    user_data = UserData.objects(user=card_id, identifier=identifier).first()
    user_data.status = 'pending'
    user_data.save()
    try:
        client = Tiyu(card_id, password)
        client.login()
        client.get_data()
    except Exception as e:
        user_data.status = 'failed'
        user_data.last_modified = datetime.datetime.now()
        user_data.save()
        print('error')
        raise e
    user_data.data = client.to_json()
    user_data.status = 'success'
    user_data.last_modified = datetime.datetime.now()
    user_data.lock_save(lock)


@users.route('/replace-avatar')
@login_required
def change_avatar():
    user = User.objects.get_or_404(card_id=current_user.id)
    user.avatar = request.args.get('avatar') + '-avatar'
    user.save()
    return jsonify(status='ok')


@users.route('/search/<query>')
def search(query):
    users = User.objects(Q(card_id__contains=query) |
                         Q(name__contains=query))[:50]
    return jsonify([{
        '_id': user.card_id,
        'name': user.name[0] + '*' * len(user.name[1:])
    }for user in users])


@users.route('/logout')
def logout():
    token = request.args.get('token')
    if token is not None:
        redis_store.delete(token)
    logout_user()
    return jsonify({
        'success': True
    })


@users.route('/<user_id>')
def profile(user_id):
    user = User.objects.get_or_404(card_id=user_id)
    return jsonify(avatar=user.avatar, nickname=user.nickname, _id=user.id)


@users.route('/<user_id>/custom', methods=['GET', 'PATCH'])
@login_required
def user_custom(user_id):
    if user_id != current_user.id:
        abort(401)
    if request.method == 'GET':
        user = User.objects.get_or_404(card_id=current_user.id)
        return jsonify(user.custom)
    else:
        user = User.objects(card_id=current_user.id).first()
        custom = json.loads(user.custom) if user.custom != '' else {}
        patch = request.get_json()
        for key in patch.keys():
            custom[key] = patch[key]
        user.custom = json.dumps(custom)
        user.save()
    return jsonify(avatar=user.avatar, nickname=user.nickname, _id=user.id)


@users.route('/set-custom-theme')
def set_custom_theme():
    theme = request.args.get('theme')
    user = User.objects(card_id=current_user.id).first()
    custom = json.loads(user.custom) if user.custom != '' else {}
    custom['theme'] = theme
    user.custom = json.dumps(custom)
    user.save()
    return jsonify({
        'status': 'ok'
    })


@users.route("/login/", methods=['GET','POST'])
def login():
    """ main user auth view function
    user was authenticated when user has valid token (which stored in redis),
    or has valid cardID and password
    """
    # TODO: remove token-login after JWT was introduced
    if request.method == 'GET':
        token = request.args.get('token')
        card_id = redis_store.get('token:' + token)
        if card_id is None:
            abort(403)
        user = User.objects(card_id=card_id).first()
        result = user.login(token)
        redis_store.set('token:' + token, user.card_id, ex=864000)
        login_user(user)
    else:
        post_data = request.get_json()
        user = User.objects(card_id=post_data['card_id']).first()
        need_fresh = False
        if user is not None:
            need_fresh = not user.authenticate(post_data['password'])
        else:
            user = User(card_id=post_data['card_id'])
            need_fresh = True
        if need_fresh and not user.regisiter(post_data['password']):
            abort(403)
        token = make_token()
        result = user.login(token)
        redis_store.set('token:' + token, post_data['card_id'], ex=864000)
        login_user(user)
    return jsonify(result)
