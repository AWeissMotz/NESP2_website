from flask import Blueprint, render_template
from flask_login import login_required
bp = Blueprint('about', __name__)


@bp.route('/about')
@login_required
def about():
    return render_template('about.html')
