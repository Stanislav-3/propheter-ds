from flask import Flask
from api.helloworld import hello_world


app = Flask(__name__)
app.add_url_rule('/', view_func=hello_world, methods=['GET'])


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
