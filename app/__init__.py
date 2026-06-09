from flask import Flask
from concurrent.futures import ThreadPoolExecutor

#App-level executor for async jobs
executor = ThreadPoolExecutor(max_workers=4)

def create_app():
    app = Flask(__name__)
    
    from app.routes import bp
    app.register_blueprint(bp)

    return app
