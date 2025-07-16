from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask Test Server</h1><p>This is working!</p>'

@app.route('/test')
def test():
    return 'Test endpoint working!'

if __name__ == '__main__':
    print("Starting Flask test server...")
    print("Open: http://localhost:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
