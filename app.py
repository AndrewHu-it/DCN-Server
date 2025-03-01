from app import create_app

# TODO: construct a config using environment variables

# TODO: pass the config into the app
app = create_app()

if __name__ == '__main__':
    print('Starting server...')
    app.run(host='0.0.0.0', port=5000)