from app import app

@app.route('/')
def get_info():
    return 'return some information'
