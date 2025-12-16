from flask import jsonify, request
from src.config.db import session
from src.models.book import Book


def init_api_routes(app):
    # --- READ (GET ALL) --- [cite: 100, 181]
    @app.route('/api/books', methods=['GET'])
    def get_books():
        books = session.query(Book).all()
        # Convertimos los objetos a lista de diccionarios
        books_list = []
        for book in books:
            books_list.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'year': book.year
            })
        return jsonify(books_list)

    # --- READ ONE (GET BY ID) --- [cite: 101, 190]
    @app.route('/api/books/<book_id>', methods=['GET'])
    def get_book_by_id(book_id):
        book = session.query(Book).filter_by(id=book_id).first()

        if book is None:
            return jsonify({"error": "Not Found"}), 404
        else:
            return jsonify({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'year': book.year
            })

    # --- CREATE (POST) --- [cite: 103, 207]
    @app.route('/api/books', methods=['POST'])
    def create_book():
        book_data = request.get_json()  # [cite: 208]

        new_book = Book(
            title=book_data['title'],
            author=book_data['author'],
            year=book_data['year']
        )

        session.add(new_book)
        session.commit()  # Guardamos cambios en BBDD

        return jsonify({
            'id': new_book.id,
            'message': 'Book created successfully'
        }), 201

    # --- UPDATE (PUT) --- [cite: 104, 215]
    @app.route('/api/books/<book_id>', methods=['PUT'])
    def update_book(book_id):
        book_data = request.get_json()
        book_bd = session.query(Book).filter_by(id=book_id).first()

        if book_bd is None:
            return jsonify({"error": "Not Found"}), 404
        else:
            # Actualizamos solo si el dato viene en el JSON
            book_bd.title = book_data.get("title", book_bd.title)
            book_bd.author = book_data.get("author", book_bd.author)
            book_bd.year = book_data.get("year", book_bd.year)

            session.commit()

            return jsonify({
                'id': book_bd.id,
                'title': book_bd.title,
                'author': book_bd.author,
                'year': book_bd.year
            }), 200

    # --- DELETE (DELETE) --- [cite: 105, 222]
    @app.route('/api/books/<book_id>', methods=['DELETE'])
    def delete_book(book_id):
        book = session.query(Book).filter_by(id=book_id).first()

        if book is None:
            return jsonify({"error": "Not Found"}), 404
        else:
            session.delete(book)
            session.commit()
            return jsonify({"message": "Deleted"}), 204