from flask import Flask, render_template

marketApp = Flask(__name__)


@marketApp.route('/')
def index():
    return render_template('index.html')




if __name__ == '__main__':
    marketApp.run(debug=True)