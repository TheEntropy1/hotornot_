
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            rating_sum INTEGER DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, filename, rating_sum, rating_count FROM photos')
    photos = c.fetchall()
    conn.close()
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        return 'No file uploaded', 400
    photo = request.files['photo']
    if photo.filename == '':
        return 'No selected file', 400
    filename = photo.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    photo.save(filepath)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO photos (filename) VALUES (?)', (filename,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/rate/<int:photo_id>', methods=['POST'])
def rate(photo_id):
    rating = int(request.form['rating'])
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE photos SET rating_sum = rating_sum + ?, rating_count = rating_count + 1 WHERE id = ?', (rating, photo_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/meetme')
def meetme():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, filename FROM photos ORDER BY RANDOM() LIMIT 1')
    photo = c.fetchone()
    conn.close()
    return render_template('meetme.html', photo=photo)

@app.route('/hotlist')
def hotlist():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, filename, rating_sum, rating_count, (rating_sum * 1.0 / rating_count) as avg_rating FROM photos WHERE rating_count > 0 ORDER BY avg_rating DESC LIMIT 10')
    photos = c.fetchall()
    conn.close()
    return render_template('hotlist.html', photos=photos)

@app.route('/announce')
def announce():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    three_days_ago = datetime.now() - timedelta(days=3)
    c.execute('SELECT id, filename, (rating_sum * 1.0 / rating_count) as avg_rating FROM photos WHERE uploaded_at <= ? ORDER BY avg_rating DESC LIMIT 1', (three_days_ago,))
    winner = c.fetchone()
    conn.close()
    if winner:
        return f"The winner is: {winner[1]} with average rating {winner[2]:.2f}!"
    else:
        return "No winner yet. Try later."

if __name__ == '__main__':
    app.run(debug=True)
