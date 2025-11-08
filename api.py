#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import logging
import hashlib
import re
import uuid
from datetime import datetime
from argparse import ArgumentParser
from abc import abstractmethod, ABC
from http.server import BaseHTTPRequestHandler, HTTPServer
from dateutil.relativedelta import relativedelta

from scoring import get_interests, get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}

class Field(ABC):
    def __init__(self, required, nullable=False):
        self.required = required
        self.nullable = nullable

    def is_valid(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required and cannot be None")
            return False
        if value == "" and not self.nullable:
            raise ValueError("Field cannot be empty")
        return True
    @abstractmethod
    def validate(self, value):
        ...


class CharField(Field):
    def validate(self, value):
        self.is_valid(value)
        if value:
            if not isinstance(value, str):
                raise ValueError("Field must be a string")


class ArgumentsField(Field):
    def validate(self, value):
        self.is_valid(value)
        if not isinstance(value, dict):
            raise ValueError("Arguments must be a valid json")


class EmailField(Field):
    def validate(self, value):
        self.is_valid(value)
        if value:
            if not re.match(r'.+@.+', value):
                raise ValueError("Email must be a valid email address")


class PhoneField(Field):
    def validate(self, value):
        self.is_valid(value)
        if value:
            if not isinstance(value, (str, int)):
                raise ValueError("Phone number must be a string or an integer")
            if isinstance(value, int) and len(str(value)) != 11:
                raise ValueError("Phone number must be 11 characters long")
            if isinstance(value, str) and len(value) != 11:
                raise ValueError("Phone number must be 11 characters long")
            if str(value)[0] != "7":
                raise ValueError("Phone number must start with 7")





class DateField(Field):
    def validate(self, value):
        self.is_valid(value)
        if value:
            try:
                datetime.strptime(value, "%d.%m.%Y")
            except ValueError:
                raise ValueError("Invalid date. Date must be in format DD.MM.YYYY")


class BirthDayField(Field):
    def validate(self, value):
        self.is_valid(value)
        if value:
            try:
                date = datetime.strptime(value, "%d.%m.%Y")
            except ValueError:
                raise ValueError("Invalid date. Date must be in format DD.MM.YYYY")
            if date < datetime.today()- relativedelta(years=70):
                raise ValueError("Invalid date")


class GenderField(Field):
    def validate(self, value):
        self.is_valid(value)
        if value:
            if not isinstance(value, int) or value not in [0, 1, 2]:
                raise ValueError("Invalid gender")


class ClientIDsField(Field):
    def validate(self, value):
        self.is_valid(value)
        if not isinstance(value, list):
            raise ValueError("client_ids should be a list")
        if len(value) == 0:
            raise ValueError("client_ids cannot be an empty list")
        for number in value:
            if not isinstance(number, int):
                raise ValueError("client_ids should be an int")
        return value

class BaseRequest:
    def __init__(self, **kwargs):
        self.errors = {}
        self.fields = {}
        self.raw_data = kwargs or {}

        for name, field in self.__class__.__dict__.items():
            if not isinstance(field, Field):
                continue
            self.fields[name] = field
            value = kwargs.get(name)
            try:
                field.validate(value)
            except ValueError as e:
                self.errors[name] = str(e)
            else:
                setattr(self, name, value)

    def is_valid(self):
        return len(self.errors) == 0


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        if not self.is_valid():
            return False

        valid_pairs = [
            ("phone", "email"),
            ("first_name", "last_name"),
            ("gender", "birthday")
        ]
        has_valid_pair = False

        for left_name, right_name in valid_pairs:
            left_val = getattr(self, left_name, None)
            right_val = getattr(self, right_name, None)
            if left_val is not None and right_val is not None:
                has_valid_pair = True
                break
        return has_valid_pair

class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    body = request.get("body", {})
    method_request = MethodRequest(**body)

    if not method_request.is_valid():
        return {"error": method_request.errors}, INVALID_REQUEST

    if not check_auth(method_request):
        return {"error": "Forbidden"}, FORBIDDEN
    ctx["has"] = []

    if method_request.method == "online_score":
        args_dict = method_request.arguments
        arguments = OnlineScoreRequest(**args_dict)
        if not arguments.validate():
            return {"error": arguments.errors}, INVALID_REQUEST
        ctx["has"] = list(arguments.raw_data.keys())
        try:
            score = get_score(store, **args_dict)
        except Exception:
            score = 0.0
        if method_request.is_admin:
            score = 42

        ctx["score"] = score
        return {"score": score}, OK

    elif method_request.method == "clients_interests":
        args_dict = method_request.arguments or {}
        arguments = ClientsInterestsRequest(**args_dict)
        if not arguments.is_valid():
            return {"error": arguments.errors}, INVALID_REQUEST

        result = {}
        for cid in arguments.client_ids:
            interests = get_interests(store, cid)
            result[str(cid)] = interests
        ctx["nclients"] = len(arguments.client_ids)
        return result, OK

    else:
        return {"error": "Unknown method"}, INVALID_REQUEST


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()