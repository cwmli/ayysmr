from ayysmr_web import create_app

if __name__ == '__main__':
    app = create_app('app')
    app.run(host='0.0.0.0', port=5000)