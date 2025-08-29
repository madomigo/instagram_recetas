from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import settings
from db_sqlite import (
    fetch_all_recipes, fetch_recipe, upsert_recipe, delete_recipe, init_db,
    get_folders, create_folder, delete_folder_by_name
)
from scraper import scrape_instagram_post, ScrapeError

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY

@app.route('/')
def index():
    recipes = fetch_all_recipes()
    folders = get_folders()
    return render_template('index.html', recipes=recipes, folders=folders)

@app.route('/folder/<folder_name>')
def folder(folder_name):
    recipes = fetch_all_recipes()
    filtered = [r for r in recipes if (r['folder'] or 'General') == folder_name]
    folders = get_folders()
    return render_template('folder.html', recipes=filtered, folders=folders, current_folder=folder_name)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        title = request.form.get('title', '').strip() or None
        folder_select = request.form.get('folder_select')
        new_folder_name = request.form.get('new_folder_name','').strip()
        folder = None
        if folder_select == 'new' and new_folder_name:
            create_folder(new_folder_name)
            folder = new_folder_name
        elif folder_select and folder_select != 'none':
            folder = folder_select

        try:
            data = scrape_instagram_post(url)
        except ScrapeError as e:
            flash(f'Error al obtener datos del post: {e}', 'danger')
            return redirect(url_for('add'))

        recipe = {
            'url': url,
            'shortcode': data.get('shortcode'),
            'author': data.get('author'),
            'caption': data.get('caption'),
            'image_bytes': data.get('image_bytes'),
            'video_bytes': data.get('video_bytes'),
            'posted_at': data.get('posted_at'),
            'likes': data.get('likes'),
            'title': title,
            'folder': folder
        }
        upsert_recipe(recipe)
        flash('Receta añadida correctamente', 'success')
        return redirect(url_for('index'))

    folders = get_folders()
    return render_template('add.html', folders=folders)

@app.route('/recipe/<int:recipe_id>')
def detail(recipe_id):
    recipe = fetch_recipe(recipe_id)
    if not recipe:
        flash("Receta no encontrada", "warning")
        return redirect(url_for('index'))
    folders = get_folders()
    return render_template('detail.html', r=recipe, folders=folders)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete(recipe_id):
    delete_recipe(recipe_id)
    flash("Receta eliminada", "info")
    return redirect(url_for('index'))

@app.route('/folders/create', methods=['POST'])
def api_create_folder():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'ok': False, 'error': 'Nombre vacío'}), 400
    folder_id = create_folder(name)
    return jsonify({'ok': True, 'name': name})

@app.route('/folders/delete', methods=['POST'])
def api_delete_folder():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'ok': False, 'error': 'Falta nombre'}), 400
    delete_folder_by_name(name)
    return jsonify({'ok': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
