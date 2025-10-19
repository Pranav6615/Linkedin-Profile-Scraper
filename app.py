from flask import Flask, render_template_string, request, redirect, url_for, send_file, jsonify
import csv, os, time, random
from werkzeug.utils import secure_filename
from playwright.sync_api import sync_playwright

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '.'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
ALLOWED_EXTENSIONS = {'csv'}

INPUT_CSV_PATH = 'profiles.csv'
OUTPUT_CSV_PATH = 'scraped_data.csv'
AUTH_FILE_PATH = 'state.json'
LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'

# --- HTML Templates ---
HTML_HOME = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>LinkedIn Scraper - Upload CSV</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-800">
<div class="container mx-auto p-6">
<h1 class="text-3xl font-bold mb-4">Upload Profiles CSV 🚀</h1>
<form action="/upload" method="post" enctype="multipart/form-data" class="bg-white shadow rounded p-6">
  <input type="file" name="file" accept=".csv" class="mb-4"/>
  <button type="submit" class="bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700">Upload</button>
</form>
</div>
</body>
</html>
"""

HTML_RESULTS = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>LinkedIn Scraper Results</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body { font-family: Inter, sans-serif; }.table-container { max-height: 70vh; overflow-y: auto; } td { word-wrap: break-word; max-width: 300px; }</style>
</head>
<body class="bg-gray-100 text-gray-800">
<div class="container mx-auto p-6">
<h1 class="text-3xl font-bold mb-4">LinkedIn Scraper Results 🚀</h1>
<div><a href="/download" class="inline-block bg-blue-600 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-200">Download as CSV</a></div>
<div class="table-container bg-white shadow rounded p-4 mt-4">
<table class="min-w-full">
<thead class="sticky top-0 bg-gray-200">
<tr>{% for header in headers %}<th class="py-2 px-4 text-left">{{ header.replace('_',' ')|title }}</th>{% endfor %}</tr>
</thead>
<tbody>
{% for row in data %}
<tr class="hover:bg-gray-50">{% for header in headers %}<td class="py-2 px-4 border-b whitespace-pre-wrap">{{ row[header] }}</td>{% endfor %}</tr>
{% endfor %}
{% if not data %}<tr><td colspan="{{ headers|length }}" class="py-4 px-4 text-center text-gray-500">No data scraped yet. Run <a href="/start_scrape" class="text-blue-600 underline">/start_scrape</a> to begin scraping.</td></tr>{% endif %}
</tbody>
</table>
</div>
</div>
</body>
</html>"""

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitizetext(text):
    if not isinstance(text, str) or text == "NA": return "NA"
    return ' '.join(text.split())

# --- Your existing scrape_profile_page function ---
def scrape_profile_page(page, profileurl):
    data = {
        "url": profileurl,
        "name": "NA",
        "profiletitle": "NA",
        "about": "NA",
        "currentcompany": "NA",
        "currentjobtitle": "NA",
        "currentjobduration": "NA",
        "currentjobdescription": "NA",
        "lastcompany": "NA",
        "lastjobtitle": "NA",
        "lastjobduration": "NA",
        "lastjobdescription": "NA"
    }
    try:
        page.goto(profileurl, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_selector('h1', timeout=30000)
        time.sleep(random.uniform(1.5, 3.5))

        # Name and Profile Title
        try:
            data["name"] = sanitizetext(page.locator("h1").first.inner_text().strip())
        except:
            pass
        try:
            data["profiletitle"] = sanitizetext(page.locator("div.text-body-medium.break-words").first.inner_text().strip())
        except:
            pass

        # About
        try:
            about_text = ""
            about_spans = page.locator('section:has(h2:has-text("About")) span[aria-hidden="true"]')
            for i in range(about_spans.count()):
                part = about_spans.nth(i).inner_text().strip()
                if part: about_text += " " + part
            data["about"] = sanitizetext(about_text)
        except:
            pass

        # Experience
        try:
            exp_section = page.locator("section:has(h2:has-text('Experience'))")
            exp_items = exp_section.locator("ul > li").all()
            jobs = []
            for item in exp_items:
                sub_roles = item.locator("ul > li").all()
                if len(sub_roles) > 0:
                    company = "NA"
                    parent_duration = "NA"
                    try:
                        info_spans = item.locator("span[aria-hidden='true']")
                        if info_spans.count() > 0:
                            company = info_spans.nth(0).inner_text().strip()
                        duration_span = item.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
                        if duration_span.count() > 0:
                            parent_duration = duration_span.inner_text().strip()
                    except: pass

                    for sub in sub_roles:
                        jobtitle = description = "NA"
                        duration = parent_duration
                        try:
                            info_spans = sub.locator("span[aria-hidden='true']")
                            if info_spans.count() > 0:
                                jobtitle = info_spans.nth(0).inner_text().strip()
                        except: pass
                        try:
                            duration_span = sub.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
                            if duration_span.count() > 0:
                                duration = duration_span.inner_text().strip()
                        except: pass
                        try:
                            desc_span = sub.locator("div.inline-show-more-text span[aria-hidden='true'], div.inline-show-more-text span.visually-hidden").first
                            if desc_span.count() > 0:
                                description = desc_span.inner_text().strip()
                        except: pass

                        jobs.append({
                            "company": sanitizetext(company),
                            "jobtitle": sanitizetext(jobtitle),
                            "duration": sanitizetext(duration),
                            "description": sanitizetext(description)
                        })
                else:
                    company = jobtitle = duration = description = "NA"
                    try:
                        info_spans = item.locator("span[aria-hidden='true']")
                        if info_spans.count() > 1:
                            jobtitle = info_spans.nth(0).inner_text().strip()
                            company_raw = info_spans.nth(1).inner_text().strip()
                            for sep in ['·', '.', '•']:
                                if sep in company_raw:
                                    company = company_raw.split(sep)[0].strip()
                                    break
                            else:
                                company = company_raw
                        elif info_spans.count() == 1:
                            jobtitle = info_spans.nth(0).inner_text().strip()
                    except: pass
                    try:
                        duration_span = item.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
                        if duration_span.count() > 0:
                            duration = duration_span.inner_text().strip()
                    except: pass
                    try:
                        desc_span = item.locator("div.inline-show-more-text span[aria-hidden='true'], div.inline-show-more-text span.visually-hidden").first
                        if desc_span.count() > 0:
                            description = desc_span.inner_text().strip()
                    except: pass

                    jobs.append({
                        "company": sanitizetext(company),
                        "jobtitle": sanitizetext(jobtitle),
                        "duration": sanitizetext(duration),
                        "description": sanitizetext(description)
                    })

            if len(jobs) > 0:
                data["currentcompany"] = jobs[0]["company"]
                data["currentjobtitle"] = jobs[0]["jobtitle"]
                data["currentjobduration"] = jobs[0]["duration"]
                data["currentjobdescription"] = jobs[0]["description"]
            if len(jobs) > 1:
                data["lastcompany"] = jobs[1]["company"]
                data["lastjobtitle"] = jobs[1]["jobtitle"]
                data["lastjobduration"] = jobs[1]["duration"]
                data["lastjobdescription"] = jobs[1]["description"]
            if data["profiletitle"] == "NA" and data["currentjobtitle"] != "NA":
                data["profiletitle"] = data["currentjobtitle"]
        except Exception as e:
            print(f"Experience parse error: {e}")
    except Exception as e:
        print(f"Profile scrape error for {profileurl}: {e}")
        return None
    return data

def scrape_all_profiles():
    scrapeddata = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        if os.path.exists(AUTH_FILE_PATH):
            context = browser.new_context(storage_state=AUTH_FILE_PATH)
        else:
            context = browser.new_context()
            page = context.new_page()
            page.goto(LINKEDIN_LOGIN_URL)
            print("Login manually in the opened browser and press ENTER...")
            input()
            context.storage_state(path=AUTH_FILE_PATH)

        page = context.new_page()
        with open(INPUT_CSV_PATH, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            profileurls = [row[0] for row in reader if row]
        for i, url in enumerate(profileurls):
            data = scrape_profile_page(page, url)
            if data:
                scrapeddata.append(data)
        browser.close()

    if scrapeddata:
        fieldnames = scrapeddata[0].keys()
        with open(OUTPUT_CSV_PATH, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scrapeddata)
    return scrapeddata

# --- Flask Routes ---
@app.route("/", methods=["GET"])
def homepage():
    return render_template_string(HTML_HOME)

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(INPUT_CSV_PATH)
        return redirect("/results")
    return "Invalid file type", 400

@app.route("/results")
def results():
    if os.path.exists(OUTPUT_CSV_PATH):
        with open(OUTPUT_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        headers = reader.fieldnames
        return render_template_string(HTML_RESULTS, data=data, headers=headers)
    # Show uploaded CSV info if scraping not yet run
    elif os.path.exists(INPUT_CSV_PATH):
        with open(INPUT_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            count = sum(1 for _ in reader)
        return f"CSV uploaded successfully! {count} profiles ready to scrape. Run <a href='/start_scrape'>/start_scrape</a>."
    headers = ["url","name","profiletitle","about","currentcompany","currentjobtitle","currentjobduration","currentjobdescription","lastcompany","lastjobtitle","lastjobduration","lastjobdescription"]
    return render_template_string(HTML_RESULTS, data=[], headers=headers)

@app.route("/start_scrape")
def start_scrape():
    try:
        data = scrape_all_profiles()
        return redirect("/results")
    except Exception as e:
        return f"Scraping error: {e}"

@app.route("/download")
def download():
    if os.path.exists(OUTPUT_CSV_PATH):
        return send_file(OUTPUT_CSV_PATH, as_attachment=True)
    return "No file available. Upload CSV and scrape first."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

