# import csv
# import os
# import time
# import random
# from flask import Flask
# from playwright.sync_api import sync_playwright

# # --- Configuration ---
# INPUT_CSV_PATH = 'profiles.csv'
# OUTPUT_CSV_PATH = 'scraped_data.csv'
# AUTH_FILE_PATH = 'state.json'
# LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'
# # MAX_PROFILES_PER_SESSION has been removed to process all profiles.

# # --- Flask HTML Template ---
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8" />
#     <meta name="viewport" content="width=device-width, initial-scale=1" />
#     <title>LinkedIn Scraper Results</title>
#     <script src="https://cdn.tailwindcss.com"></script>
#     <style>
#         body { font-family: Inter, sans-serif; }
#         .table-container { max-height: 70vh; overflow-y: auto; }
#         td { word-wrap: break-word; max-width: 300px; }
#     </style>
# </head>
# <body class="bg-gray-100 text-gray-800">
#     <div class="container mx-auto p-6">
#         <h1 class="text-3xl font-bold mb-4">LinkedIn Scraper Results 🚀</h1>
#         <div>
#             <a href="/download" class="inline-block bg-blue-600 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-200">Download as CSV</a>
#         </div>
#         <div class="table-container bg-white shadow rounded p-4 mt-4">
#             <table class="min-w-full">
#                 <thead class="sticky top-0 bg-gray-200">
#                     <tr>
#                         {% for header in headers %}
#                         <th class="py-2 px-4 text-left">{{ header.replace('_', ' ')|title }}</th>
#                         {% endfor %}
#                     </tr>
#                 </thead>
#                 <tbody>
#                     {% for row in data %}
#                     <tr class="hover:bg-gray-50">
#                         {% for header in headers %}
#                         <td class="py-2 px-4 border-b whitespace-pre-wrap">{{ row[header] }}</td>
#                         {% endfor %}
#                     </tr>
#                     {% endfor %}
#                     {% if not data %}
#                     <tr>
#                         <td colspan="{{ headers|length }}" class="py-4 px-4 text-center text-gray-500">No data was scraped.</td>
#                     </tr>
#                     {% endif %}
#                 </tbody>
#             </table>
#         </div>
#     </div>
# </body>
# </html>
# """

# def human_like_interaction(page):
#     """Simulates varied human-like scrolling and mouse movements."""
#     try:
#         for _ in range(random.randint(2, 4)):
#             page.mouse.wheel(0, random.randint(400, 800))
#             time.sleep(random.uniform(0.5, 1.0))
#         for _ in range(random.randint(1, 3)):
#             page.keyboard.press('PageDown')
#             time.sleep(random.uniform(0.8, 1.5))
#         viewport_size = page.viewport_size
#         if viewport_size:
#             x, y = random.randint(0, viewport_size['width'] - 1), random.randint(0, viewport_size['height'] - 1)
#             page.mouse.move(x, y, steps=random.randint(5, 15))
#         time.sleep(random.uniform(2.0, 4.0))
#     except Exception as e:
#         print(f"Could not perform human-like interaction: {e}")

# def sanitizetext(text):
#     """Cleans text by removing newlines and extra spaces for clean CSV output."""
#     if not isinstance(text, str) or text == "NA":
#         return "NA"
#     return ' '.join(text.split())

# def scrape_profile_page(page, profileurl):
#     data = {
#         "url": profileurl,
#         "name": "NA",
#         "profiletitle": "NA",
#         "about": "NA",
#         "currentcompany": "NA",
#         "currentjobtitle": "NA",
#         "currentjobduration": "NA",
#         "currentjobdescription": "NA",
#         "lastcompany": "NA",
#         "lastjobtitle": "NA",
#         "lastjobduration": "NA",
#         "lastjobdescription": "NA"
#     }
#     try:
#         page.goto(profileurl, wait_until='domcontentloaded', timeout=60000)
#         page.wait_for_selector('h1', timeout=30000)
#         time.sleep(random.uniform(1.5, 3.5))

#         # Name and Profile Title
#         try:
#             data["name"] = sanitizetext(page.locator("h1").first.inner_text().strip())
#         except Exception:
#             pass
#         try:
#             data["profiletitle"] = sanitizetext(page.locator("div.text-body-medium.break-words").first.inner_text().strip())
#         except Exception:
#             pass

#         # ABOUT SECTION
#         try:
#             about_text = ""
#             # About is typically in a section with multiple text spans (visible and visually-hidden)
#             about_spans = page.locator('section:has(h2:has-text("About")) span[aria-hidden="true"]')
#             for i in range(about_spans.count()):
#                 part = about_spans.nth(i).inner_text().strip()
#                 if part:
#                     about_text += " " + part
#             data["about"] = sanitizetext(about_text)
#         except Exception:
#             pass

#         # EXPERIENCE SECTION
#         try:
#             exp_section = page.locator("section:has(h2:has-text('Experience'))")
#             exp_items = exp_section.locator("ul > li").all()
#             jobs = []

#             for item in exp_items:
#                 # Detect if this item contains grouped sub-roles
#                 sub_roles = item.locator("ul > li").all()
#                 if len(sub_roles) > 0:
#                     # --- Grouped structure (Company as parent, inner roles as children) ---
#                     company = "NA"
#                     parent_duration = "NA"
#                     try:
#                         info_spans = item.locator("span[aria-hidden='true']")
#                         if info_spans.count() > 0:
#                             company = info_spans.nth(0).inner_text().strip()
#                         duration_span = item.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
#                         if duration_span.count() > 0:
#                             parent_duration = duration_span.inner_text().strip()
#                     except:
#                         pass

#                     # Now parse each sub-role under this company
#                     for sub in sub_roles:
#                         jobtitle = description = "NA"
#                         duration = parent_duration
#                         try:
#                             info_spans = sub.locator("span[aria-hidden='true']")
#                             if info_spans.count() > 0:
#                                 jobtitle = info_spans.nth(0).inner_text().strip()
#                         except:
#                             pass
#                         try:
#                             duration_span = sub.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
#                             if duration_span.count() > 0:
#                                 duration = duration_span.inner_text().strip()
#                         except:
#                             pass
#                         try:
#                             desc_span = sub.locator("div.inline-show-more-text span[aria-hidden='true'], div.inline-show-more-text span.visually-hidden").first
#                             if desc_span.count() > 0:
#                                 description = desc_span.inner_text().strip()
#                         except:
#                             pass

#                         jobs.append({
#                             "company": sanitizetext(company),
#                             "jobtitle": sanitizetext(jobtitle),
#                             "duration": sanitizetext(duration),
#                             "description": sanitizetext(description)
#                         })

#                 else:
#                     # --- Flat structure (single role, your existing logic) ---
#                     company = jobtitle = duration = description = "NA"
#                     try:
#                         info_spans = item.locator("span[aria-hidden='true']")
#                         if info_spans.count() > 1:
#                             jobtitle = info_spans.nth(0).inner_text().strip()
#                             company_raw = info_spans.nth(1).inner_text().strip()
#                             for sep in ['·', '.', '•']:
#                                 if sep in company_raw:
#                                     company = company_raw.split(sep)[0].strip()
#                                     break
#                             else:
#                                 company = company_raw
#                         elif info_spans.count() == 1:
#                             jobtitle = info_spans.nth(0).inner_text().strip()
#                     except:
#                         pass

#                     try:
#                         duration_span = item.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
#                         if duration_span.count() > 0:
#                             duration = duration_span.inner_text().strip()
#                     except:
#                         pass

#                     try:
#                         desc_span = item.locator("div.inline-show-more-text span[aria-hidden='true'], div.inline-show-more-text span.visually-hidden").first
#                         if desc_span.count() > 0:
#                             description = desc_span.inner_text().strip()
#                     except:
#                         pass

#                     jobs.append({
#                         "company": sanitizetext(company),
#                         "jobtitle": sanitizetext(jobtitle),
#                         "duration": sanitizetext(duration),
#                         "description": sanitizetext(description)
#                     })

#             # --- Assign top jobs to output fields ---
#             if len(jobs) > 0:
#                 data["currentcompany"] = jobs[0]["company"]
#                 data["currentjobtitle"] = jobs[0]["jobtitle"]
#                 data["currentjobduration"] = jobs[0]["duration"]
#                 data["currentjobdescription"] = jobs[0]["description"]

#             if len(jobs) > 1:
#                 data["lastcompany"] = jobs[1]["company"]
#                 data["lastjobtitle"] = jobs[1]["jobtitle"]
#                 data["lastjobduration"] = jobs[1]["duration"]
#                 data["lastjobdescription"] = jobs[1]["description"]

#             if data["profiletitle"] == "NA" and data["currentjobtitle"] != "NA":
#                 data["profiletitle"] = data["currentjobtitle"]

#         except Exception as e:
#             print(f"Experience section parse error: {e}")


#     except Exception as e:
#         print(f"Profile scrape error for {profileurl}: {e}")
#         return None

#     return data




# def main():
#     with open(INPUT_CSV_PATH, 'r', encoding='utf-8') as infile:
#         reader = csv.reader(infile)
#         profileurls = [row[0] for row in reader if row]

#     print(f"Processing {len(profileurls)} profiles from CSV...")

#     scrapeddata = []
#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=False)

#             # --- Check for saved login state ---
#             if os.path.exists(AUTH_FILE_PATH):
#                 print("✅ Using existing login session from state.json...")
#                 context = browser.new_context(storage_state=AUTH_FILE_PATH)
#             else:
#                 print("⚠️ No saved session found. Opening LinkedIn login page...")
#                 context = browser.new_context()
#                 page = context.new_page()
#                 page.goto(LINKEDIN_LOGIN_URL)
#                 print("🔑 Please log in to LinkedIn manually in the opened window.")
#                 print("After successful login, press ENTER here to continue...")
#                 input()
#                 context.storage_state(path=AUTH_FILE_PATH)
#                 print("💾 Login session saved as state.json")

#             page = context.new_page()
#             try:
#                 for i, url in enumerate(profileurls):
#                     print(f"[{i+1}/{len(profileurls)}] Scraping: {url}")
#                     if not url.startswith('http'):
#                         print("  - Invalid URL, skipping.")
#                         continue
#                     data = scrape_profile_page(page, url)
#                     if data:
#                         scrapeddata.append(data)
#                         print(f"  - Scraped: {data.get('name', 'Unknown')} / {data.get('profiletitle', 'Unknown')}")
#                     if i < len(profileurls) - 1:
#                         sleeptime = random.uniform(25, 60)
#                         print(f"  - Sleeping {sleeptime:.1f}s before next profile...")
#                         time.sleep(sleeptime)
#             except KeyboardInterrupt:
#                 print("\nInterrupted! Saving progress so far...")
#             finally:
#                 if scrapeddata:
#                     fieldnames = scrapeddata[0].keys()
#                     with open(OUTPUT_CSV_PATH, 'w', encoding='utf-8', newline='') as outfile:
#                         writer = csv.DictWriter(outfile, fieldnames=fieldnames)
#                         writer.writeheader()
#                         for row in scrapeddata:
#                             writer.writerow(row)
#                     print(f"Saved {len(scrapeddata)} scraped profiles to {OUTPUT_CSV_PATH}")
#             browser.close()
#     except Exception as e:
#         print(f"Playwright setup error: {e}")

#     print("Done.")

# if __name__ == "__main__":
#     main()

from flask import Flask, render_template_string, send_file, jsonify
import csv, os, time, random
from playwright.sync_api import sync_playwright

app = Flask(__name__)

INPUT_CSV_PATH = 'profiles.csv'
OUTPUT_CSV_PATH = 'scraped_data.csv'
AUTH_FILE_PATH = 'state.json'
LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'

HTML_TEMPLATE = """<!DOCTYPE html>
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
{% if not data %}<tr><td colspan="{{ headers|length }}" class="py-4 px-4 text-center text-gray-500">No data was scraped.</td></tr>{% endif %}
</tbody>
</table>
</div>
</div>
</body>
</html>"""

# --- Helper Functions ---
def sanitizetext(text):
    if not isinstance(text, str) or text == "NA": return "NA"
    return ' '.join(text.split())

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
        except Exception:
            pass
        try:
            data["profiletitle"] = sanitizetext(page.locator("div.text-body-medium.break-words").first.inner_text().strip())
        except Exception:
            pass

        # ABOUT SECTION
        try:
            about_text = ""
            # About is typically in a section with multiple text spans (visible and visually-hidden)
            about_spans = page.locator('section:has(h2:has-text("About")) span[aria-hidden="true"]')
            for i in range(about_spans.count()):
                part = about_spans.nth(i).inner_text().strip()
                if part:
                    about_text += " " + part
            data["about"] = sanitizetext(about_text)
        except Exception:
            pass

        # EXPERIENCE SECTION
        try:
            exp_section = page.locator("section:has(h2:has-text('Experience'))")
            exp_items = exp_section.locator("ul > li").all()
            jobs = []

            for item in exp_items:
                # Detect if this item contains grouped sub-roles
                sub_roles = item.locator("ul > li").all()
                if len(sub_roles) > 0:
                    # --- Grouped structure (Company as parent, inner roles as children) ---
                    company = "NA"
                    parent_duration = "NA"
                    try:
                        info_spans = item.locator("span[aria-hidden='true']")
                        if info_spans.count() > 0:
                            company = info_spans.nth(0).inner_text().strip()
                        duration_span = item.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
                        if duration_span.count() > 0:
                            parent_duration = duration_span.inner_text().strip()
                    except:
                        pass

                    # Now parse each sub-role under this company
                    for sub in sub_roles:
                        jobtitle = description = "NA"
                        duration = parent_duration
                        try:
                            info_spans = sub.locator("span[aria-hidden='true']")
                            if info_spans.count() > 0:
                                jobtitle = info_spans.nth(0).inner_text().strip()
                        except:
                            pass
                        try:
                            duration_span = sub.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
                            if duration_span.count() > 0:
                                duration = duration_span.inner_text().strip()
                        except:
                            pass
                        try:
                            desc_span = sub.locator("div.inline-show-more-text span[aria-hidden='true'], div.inline-show-more-text span.visually-hidden").first
                            if desc_span.count() > 0:
                                description = desc_span.inner_text().strip()
                        except:
                            pass

                        jobs.append({
                            "company": sanitizetext(company),
                            "jobtitle": sanitizetext(jobtitle),
                            "duration": sanitizetext(duration),
                            "description": sanitizetext(description)
                        })

                else:
                    # --- Flat structure (single role, your existing logic) ---
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
                    except:
                        pass

                    try:
                        duration_span = item.locator("span.pvs-entity__caption-wrapper[aria-hidden='true']").first
                        if duration_span.count() > 0:
                            duration = duration_span.inner_text().strip()
                    except:
                        pass

                    try:
                        desc_span = item.locator("div.inline-show-more-text span[aria-hidden='true'], div.inline-show-more-text span.visually-hidden").first
                        if desc_span.count() > 0:
                            description = desc_span.inner_text().strip()
                    except:
                        pass

                    jobs.append({
                        "company": sanitizetext(company),
                        "jobtitle": sanitizetext(jobtitle),
                        "duration": sanitizetext(duration),
                        "description": sanitizetext(description)
                    })

            # --- Assign top jobs to output fields ---
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
            print(f"Experience section parse error: {e}")


    except Exception as e:
        print(f"Profile scrape error for {profileurl}: {e}")
        return None

    return data

def scrape_all_profiles():
    scrapeddata = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
            data = scrape_profile_page(page, url)  # Your existing function
            if data:
                scrapeddata.append(data)
        browser.close()
    # Save CSV
    if scrapeddata:
        fieldnames = scrapeddata[0].keys()
        with open(OUTPUT_CSV_PATH, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scrapeddata)
    return scrapeddata

# --- Flask Routes ---
@app.route("/start_scrape")
def start_scrape():
    try:
        data = scrape_all_profiles()
        return jsonify({"status": "success", "count": len(data)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/results")
def results():
    if os.path.exists(OUTPUT_CSV_PATH):
        with open(OUTPUT_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        headers = reader.fieldnames
        return render_template_string(HTML_TEMPLATE, data=data, headers=headers)
    return "No results yet. Run /start_scrape first."

@app.route("/download")
def download():
    if os.path.exists(OUTPUT_CSV_PATH):
        return send_file(OUTPUT_CSV_PATH, as_attachment=True)
    return "No file available. Run /start_scrape first."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
