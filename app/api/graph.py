from app.data_sources.time_parse import parse_file
from flask import Blueprint

graph_bp = Blueprint("graph_bp", __name__)


@graph_bp.route("/graph/", methods=["GET"])
def json_graph():
    data = parse_file()
    return data
