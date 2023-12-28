# restapi2.py (or your Flask application file)

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:1234@localhost:3306/restapi'  # Replace with your MySQL database connection details
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    books = db.relationship('Book', backref='category', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

#Read the data
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    book_list = [{'id': book.id, 'title': book.title, 'author': book.author} for book in books]
    return jsonify(book_list)

#Get the data by book_id
@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if book:
        return jsonify({'id': book.id, 'title': book.title, 'author': book.author})
    return {'error': 'Book not found'}, 404

#Get the data by category_id
@app.route('/books/category/<int:category_id>', methods=['GET'])
def get_books_by_category(category_id):
    # Fetch books based on category_id
    books = Book.query.filter_by(category_id=category_id).all()

    if not books:
        return {'error': 'No books found in the specified category'}, 404

    book_list = [{'id': book.id, 'title': book.title, 'author': book.author, 'category_id': book.category_id} for book in books]
    return jsonify(book_list)

#Create a data
@app.route('/books', methods=['POST'])
def create_book():
    data = request.json

    # Ensure that author, title, and category_id are provided
    if 'author' not in data or 'title' not in data or 'category_id' not in data:
        return {'error': 'Author, title, and category_id are required fields'}, 400

    # Extract author, title, and category_id from the request data
    author = data['author']
    title = data['title']
    category_id = data['category_id']

    # Check if the specified category_id exists
    category = Category.query.get(category_id)

    # If the category_id does not exist, create a default category
    if not category:
        default_category_name = f'Default Category {category_id}'
        category = Category(name=default_category_name)
        db.session.add(category)
        db.session.commit()

    # Create a new book associated with the specified category
    new_book = Book(title=title, author=author, category=category)

    db.session.add(new_book)
    db.session.commit()

    return jsonify({'id': new_book.id, 'title': new_book.title, 'author': new_book.author, 'category_id': new_book.category_id}), 201


#Update the data
@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if book:
        data = request.json
        book.title = data['title']
        book.author = data['author']

        # Check if the category_id is provided in the request
        if 'category_id' in data:
            category_id = data['category_id']
            category = Category.query.get(category_id)

            # If the category_id exists, update the associated category
            if category:
                book.category = category

        db.session.commit()
        return jsonify({'id': book.id, 'title': book.title, 'author': book.author, 'category_id': book.category_id})
    return {'error': 'Book not found'}, 404

#Delete the data
@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        category = book.category
        db.session.delete(book)
        db.session.commit()

        # Check if the category has no other books
        if category and not category.books:
            db.session.delete(category)
            db.session.commit()
            return jsonify({'message': 'Book and Category deleted successfully'})
        
        return jsonify({'message': 'Book deleted successfully'})

    return {'error': 'Book not found'}, 404

if __name__ == '__main__':
    app.run(debug=True)
