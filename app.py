from flask import Flask, render_template, request, redirect, url_for, flash
from config import settings
from db_sqlite import (
    fetch_all_recipes, fetch_recipe, upsert_recipe, delete_recipe, init_db
)
from scraper import scrape_instagram_post, ScrapeError

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY


@app.route('/')
def index():
    """Lista de carpetas existentes"""
    recipes = fetch_all_recipes()
    folders = sorted(set(r["folder"] or "General" for r in recipes))
    return render_template('index.html', folders=folders)


@app.route('/folder/<folder_name>')
def folder(folder_name):
    """Muestra todas las recetas de una carpeta"""
    recipes = [r for r in fetch_all_recipes() if (r["folder"] or "General") == folder_name]
    return render_template('folder.html', folder=folder_name, recipes=recipes)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        title_input = request.form.get('title', '').strip()
        folder_input = request.form.get('folder', '').strip() or "General"

        if not url:
            flash('Por favor, pega la URL del post.', 'warning')
            return redirect(url_for('add'))

        try:
            data = scrape_instagram_post(url)
            caption = data.get("caption") or ""

            if title_input:
                title = title_input
            else:
                first_line = caption.splitlines()[0].strip() if caption.strip() else ""
                if first_line:
                    title = first_line if len(first_line) <= 60 else (first_line[:57] + "...")
                else:
                    title = f"{data.get('author') or 'Receta'} - {data.get('shortcode')}"

            data['title'] = title
            data['folder'] = folder_input

            upsert_recipe(data)
            flash('Receta guardada correctamente ✅', 'success')
            return redirect(url_for('folder', folder_name=folder_input))

        except ScrapeError as e:
            flash(f'Error al extraer el post: {e}', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')

    return render_template('add.html')


@app.route('/folder/<folder_name>/recipe/<int:recipe_id>')
def detail(folder_name, recipe_id):
    recipe = fetch_recipe(recipe_id)
    if not recipe:
        flash("Receta no encontrada", "warning")
        return redirect(url_for('folder', folder_name=folder_name))
    return render_template('detail.html', r=recipe)


@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete(recipe_id):
    delete_recipe(recipe_id)
    flash("Receta eliminada", "info")
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
