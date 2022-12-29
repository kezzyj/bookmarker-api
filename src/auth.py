from flask import Blueprint,request,jsonify
from src.constants.http_status_codes import (HTTP_400_BAD_REQUEST,
HTTP_409_CONFLICT,HTTP_201_CREATED,HTTP_401_UNAUTHORIZED,HTTP_200_OK)
from werkzeug.security import check_password_hash,generate_password_hash
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
import validators
from src.database import User,db
from flasgger import Swagger, swag_from
from src.config.swagger import template, swagger_config

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.post('/register')
@swag_from('./docs/auth/register.yaml')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if len(password) < 8:
        return jsonify({'error':"password too short"}),HTTP_400_BAD_REQUEST
    
    if not username.isalnum() or " " in username:
        return jsonify({'error': " username should be alphanumeric and without spaces"}),HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({'error': " email is not valid"}),HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first():
        return jsonify({'error': " email already exist"}),HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first():
        return jsonify({'error': " username already exist"}),HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(username=username,email=email,password=pwd_hash)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': "User created",
        'User': {'username':username, 'email':email}
        }), HTTP_201_CREATED

@auth.post("/login")
@swag_from('./docs/auth/login.yaml')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()
    if user:
        is_pass_correct = check_password_hash(user.password, password)
        if is_pass_correct:
            referesh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'user':{
                    'referesh':referesh,
                    'access':access,
                    'username':user.username,
                    'email':user.email
                }}), HTTP_200_OK
    return jsonify({'error':'wrog credentials'}), HTTP_401_UNAUTHORIZED

@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "Username": user.username,
        "email": user.email
        }), HTTP_200_OK

@auth.get("/token/referesh")
@jwt_required(refresh=True)
def refersh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity = identity)

    return jsonify({
        "access": access
    }), HTTP_200_OK

