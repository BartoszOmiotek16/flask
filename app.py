import io
import csv
from flask import Flask, request, render_template, send_file
from google_scraper import google_search, fetch_metadata

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    max_pages = request.form.get('max_pages')
    max_pages = int(max_pages) if max_pages and max_pages.isdigit() else None

    search_results = google_search(query, max_pages=max_pages)
    results = [fetch_metadata(result["url"], result["is_sponsored"]) for result in search_results]

    si = io.StringIO()
    fieldnames = ["domain", "title", "description", "sitemap", "is_sponsored", "url"]
    writer = csv.DictWriter(si, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    writer.writerows(results)

    output = io.BytesIO(si.getvalue().encode('utf-8-sig'))
    si.close()
    filename = f"{query.replace(' ', '_')}_results.csv"
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True)
