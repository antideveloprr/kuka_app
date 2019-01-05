from flask import render_template, Flask

from init_utils import logger


def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    app.config['SECRET_KEY'] = 'secret!'
    app.threaded = True
    logger.info('initializing flask websocket app')
    return app


app = create_app()


@app.route('/')
def get_home_view():
    logger.info('redirecting to home page')
    return render_template('home.html')


@app.route('/help')
def get_help_view():
    logger.info('redirecting to help page')
    return render_template('help.html')
