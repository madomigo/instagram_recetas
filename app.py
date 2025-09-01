from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import settings
from db_sqlite import (
    fetch_recipe, upsert_recipe, delete_recipe, init_db,
    get_folders, create_folder, delete_folder_by_name,
    fetch_recipes_paginated, count_recipes, UPLOAD_FOLDER
)
from scraper import scrape_instagram_post, ScrapeError

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY

PER_PAGE = 21  # recetas por página

@app.route('/')
def index():
    page = max(1, int(request.args.get('page', 1)))
    total = count_recipes()
    recipes = fetch_recipes_paginated(limit=PER_PAGE, offset=(page-1)*PER_PAGE)
    folders = get_folders()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    return render_template('index.html', recipes=recipes, folders=folders, page=page, total_pages=total_pages)

@app.route('/folder/<folder_name>')
def folder(folder_name):
    page = max(1, int(request.args.get('page', 1)))
    total = count_recipes(folder=folder_name)
    recipes = fetch_recipes_paginated(limit=PER_PAGE, offset=(page-1)*PER_PAGE, folder=folder_name)
    folders = get_folders()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    return render_template('folder.html', recipes=recipes, folders=folders,
                           current_folder=folder_name, page=page, total_pages=total_pages)

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

        shortcode = data.get('shortcode')
        image_path = None
        video_path = None

        # Guardar siempre la imagen (thumbnail o foto del post)
        if data.get('image_bytes'):
            image_path = f"{shortcode}.jpg"
            with open(UPLOAD_FOLDER / image_path, "wb") as f:
                f.write(data['image_bytes'])

        # Guardar vídeo si existe
        if data.get('video_bytes'):
            video_path = f"{shortcode}.mp4"
            with open(UPLOAD_FOLDER / video_path, "wb") as f:
                f.write(data['video_bytes'])

        recipe = {
            'url': url,
            'shortcode': shortcode,
            'author': data.get('author'),
            'caption': data.get('caption'),
            'image_path': image_path,
            'video_path': video_path,
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

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    total = count_recipes(query=q) if q else 0
    recipes = fetch_recipes_paginated(limit=PER_PAGE, offset=(page-1)*PER_PAGE, query=q) if q else []
    folders = get_folders()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    return render_template('search.html', recipes=recipes, folders=folders, query=q,
                           page=page, total_pages=total_pages)

# Nueva ruta para cambiar carpeta de un post
@app.route('/recipe/<int:recipe_id>/change_folder', methods=['POST'])
def change_recipe_folder(recipe_id):
    new_folder = request.form.get('folder_select')
    if not new_folder:
        flash("Carpeta no válida", "warning")
    else:
        from db_sqlite import update_recipe_folder, create_folder
        # Crear carpeta si no existe
        create_folder(new_folder)
        update_recipe_folder(recipe_id, new_folder)
        flash(f"Carpeta actualizada a '{new_folder}'", "success")
    return redirect(url_for('detail', recipe_id=recipe_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
