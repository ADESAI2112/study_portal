import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key = 'auto_study_portal_secret'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn=sqlite3.connect('database.db')
    cursor=conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            board TEXT NOT NULL,
            class_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            material_type TEXT NOT NULL,
            filename TEXT NOT NULL
        )
    ''')
    
    # Check if database is empty; if so, auto-populate the master syllabus matrix for Classes 6-12
    cursor.execute('SELECT COUNT(*) FROM materials')
    if cursor.fetchone()[0]==0:
        boards =['CBSE', 'GSEB']
        classes =[f'Class {i}' for i in range(6, 13)]
        subjects_map ={
            'CBSE':['Mathematics', 'Science', 'English', 'Social Science', 'Computer Science', 'Hindi'],
            'GSEB':['Mathematics', 'Science', 'English', 'Social Science', 'Gujarati', 'Computer Studies']
        }
        types =['Textbook', 'Notes', 'Solutions', 'Sample Paper']

        default_entries =[]
        for board in boards:
            for cls in classes:
                for subj in subjects_map[board]:
                    for m_type in types:
                        title = f"{cls} {subj} {m_type} ({board})"
                        filename = "default_sample.pdf" # Placeholder for auto-mapped files
                        default_entries.append((title, board, cls, subj, m_type, filename))

        cursor.executemany('''
            INSERT INTO materials (title, board, class_name, subject, material_type, filename)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', default_entries)
        conn.commit()
    
    conn.close()

init_db()

@app.route('/')
def home():
    all_materials=Materials.query.all()
    board = request.args.get('board', 'all')
    cls = request.args.get('class', 'all')
    subject = request.args.get('subject', 'all')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM materials WHERE 1=1"
    params = []

    if board != 'all':
        query += " AND board = ?"
        params.append(board)
    if cls != 'all':
        query += " AND class_name = ?"
        params.append(cls)
    if subject != 'all':
        query += " AND subject = ?"
        params.append(subject)

    cursor.execute(query, params)
    materials = cursor.fetchall()
    conn.close()

    return render_template('index.html', materials=all_materials, selected_board=board, selected_class=cls, selected_subject=subject)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        title = request.form.get('title')
        board = request.form.get('board')
        cls = request.form.get('class')
        subject = request.form.get('subject')
        m_type = request.form.get('type')
        file = request.files.get('file')

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = "default_sample.pdf"

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO materials (title, board, class_name, subject, material_type, filename)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, board, cls, subject, m_type, filename))
        conn.commit()
        conn.close()

        flash('Study material added automatically to the catalog!', 'success')
        return redirect(url_for('admin'))

    return render_template('admin.html')

if __name__=='__main__':
    import os
    port=int(os.environ.get("PORT",5000))
    app.run(host='0.0.0.0',port=port)
