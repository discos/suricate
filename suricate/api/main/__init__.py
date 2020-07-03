from flask import Blueprint

main = Blueprint('main', __name__)

from suricate.api import views
