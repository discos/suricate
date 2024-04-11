from flask import Blueprint

main = Blueprint('main', __name__)

# pylint: disable=wrong-import-position
from suricate.api import views  # noqa: F401
# pylint: enable=wrong-import-position
