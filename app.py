from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'dev-please-change'
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'products.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/', methods=['GET'])
def index():
    q = request.args.get('q', '').strip()
    edit_id = request.args.get('edit_id', type=int)

    query = Product.query
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            db.or_(Product.name.ilike(pattern), Product.category.ilike(pattern))
        )

    products = query.order_by(Product.price).all()

    edit_product = None
    if edit_id:
        edit_product = Product.query.get(edit_id)

    total = len(products)
    avg_price = None
    if total:
        avg_price = sum(p.price for p in products) / total

    return render_template('index.html', products=products, q=q,
                           total=total, avg_price=avg_price, edit_product=edit_product)


@app.route('/edit/<int:product_id>', methods=['GET'])
def edit(product_id):
    product = Product.query.get_or_404(product_id)
    q = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', '')
    return render_template('index.html', products=Product.query.order_by(Product.price if sort_by == 'price' else Product.id).all(),
                           q=q, sort_by=sort_by, total=Product.query.count(),
                           avg_price=(sum(p.price for p in Product.query.all()) / Product.query.count() if Product.query.count() else None),
                           edit_product=product)


@app.route('/update/<int:product_id>', methods=['POST'])
def update(product_id):
    product = Product.query.get_or_404(product_id)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price_raw = request.form.get('price', '').strip()

    error = None
    if not name:
        error = 'Product name cannot be empty.'
    elif not category:
        error = 'Category cannot be empty.'
    else:
        try:
            price = float(price_raw)
            if price <= 0:
                error = 'Price must be greater than 0.'
        except ValueError:
            error = 'Price must be a number.'

    if error:
        flash(error, 'error')
        return redirect(url_for('edit', product_id=product_id))

    product.name = name
    product.category = category
    product.price = price
    db.session.commit()
    flash('Product updated.', 'success')
    return redirect(url_for('index'))


@app.route('/add', methods=['POST'])
def add():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price_raw = request.form.get('price', '').strip()

    error = None
    if not name:
        error = 'Product name cannot be empty.'
    elif not category:
        error = 'Category cannot be empty.'
    else:
        try:
            price = float(price_raw)
            if price <= 0:
                error = 'Price must be greater than 0.'
        except ValueError:
            error = 'Price must be a number.'

    if error:
        flash(error, 'error')
        return redirect(url_for('index'))

    product = Product(name=name, category=category, price=price)
    db.session.add(product)
    db.session.commit()
    flash('Product added.', 'success')
    return redirect(url_for('index'))


@app.route('/delete/<int:product_id>', methods=['POST'])
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
