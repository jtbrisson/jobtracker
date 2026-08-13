from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(__import__("os").environ.get("PORT", 5000)))
