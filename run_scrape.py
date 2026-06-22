import sys
import argparse
#command: uv run python run_scrape.py --target linkedin
# We parse the arguments just to see which site to run
parser = argparse.ArgumentParser(description="Wrapper to run scrape_jobs.py with predefined configs.")
parser.add_argument("--target", type=str, choices=["indeed", "linkedin", "apify"], required=True, 
                    help="Choose whether to run the 'indeed', 'linkedin', or 'apify' preset.")

# We use parse_known_args so that if the user passes extra args by mistake, we don't crash here.
args, _ = parser.parse_known_args()

if args.target == "indeed":
    sys.argv = [
        "scrape_jobs.py",
        "--sites", "indeed",
        "--term", '"Data Analyst" OR "AI Engineer" OR "Machine Learning" -sales -marketing -hr -recruiter -consultant',
        "--location", "Germany",
        "--job-type", "fulltime",
        "--country", "Germany",
        "--hours-old", "24",
        "--distance", "50",
        "--results", "100",
        "--offset", "0",
    ]
    print("--- Running Indeed Preset ---")
    
elif args.target == "linkedin":
    sys.argv = [
        "scrape_jobs.py",
        "--sites", "linkedin",
        "--term", "AI OR Data Science OR Machine Learning",
        "--location", "Germany",
        "--job-type", "fulltime",
        "--results", "5",
        "--distance", "50",
        "--offset", "10",
        "--linkedin-fetch-description",
        "--hours-old", "24",
    ]
    print("--- Running LinkedIn Preset ---")

elif args.target == "apify":
    import os
    import json
    from dotenv import load_dotenv
    from apify_client import ApifyClient

    load_dotenv()
    api_token = os.getenv("APIFY_API_KEY")
    if not api_token:
        print("Error: APIFY_API_KEY not found in environment variables.")
        sys.exit(1)

    client = ApifyClient(api_token)

    run_input = {
        "urls": ["https://www.linkedin.com/jobs/search?keywords=AI%2BEngineer&location=Germany&geoId=101282230&f_JT=F&position=1&pageNum=0&f_TPR=r86400"],
        "scrapeCompany": False,
        "count": 10,
        "splitByLocation": False
    }

    from datetime import datetime

    print("--- Running Apify LinkedIn Scraper ---")
    run = client.actor("hKByXkMQaC5Qt9UMN").call(run_input=run_input)

    fields_to_remove = [
        "id", "trackingId", "refId", "companyLinkedinUrl", "companyLogo",
        "descriptionHtml", "applicantsCount", "applyUrl", "inputUrl"
    ]

    results = []
    dataset_id = run.default_dataset_id if hasattr(run, "default_dataset_id") else run["defaultDatasetId"]
    for item in client.dataset(dataset_id).iterate_items():
        for field in fields_to_remove:
            item.pop(field, None)
        print(item)
        results.append(item)

    # Save JSON to jobs/apify
    output_dir_json = os.path.join("jobs", "apify")
    os.makedirs(output_dir_json, exist_ok=True)
    
    # Save TXT to jobs/input
    output_dir_txt = os.path.join("jobs", "input")
    os.makedirs(output_dir_txt, exist_ok=True)
    
    timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
    
    import re
    
    json_output_file = os.path.join(output_dir_json, f"apify_linkedIN_{timestamp}.json")
    with open(json_output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    def sanitize_filename(name):
        # Remove characters that are illegal in Windows filenames
        return re.sub(r'[\\/*?:"<>|]', "_", str(name)).strip()

    def format_job_to_text(job_item):
        lines = []
        for key, value in job_item.items():
            lines.append(f"{key}:")
            if isinstance(value, str):
                lines.append(value.strip())
            else:
                lines.append(str(value))
            lines.append("")
        return "\n".join(lines)

    for item in results:
        company = sanitize_filename(item.get("companyName", "UnknownCompany"))
        title = sanitize_filename(item.get("title", "UnknownTitle"))
        
        filename = f"{company}_{title}.txt"
        txt_output_file = os.path.join(output_dir_txt, filename)
        
        with open(txt_output_file, "w", encoding="utf-8") as f:
            f.write(format_job_to_text(item))
            
    print(f"\nSaved JSON with {len(results)} jobs to {json_output_file}")
    print(f"Created {len(results)} individual text files in {output_dir_txt}")
    sys.exit(0)

# Import and run the actual script for JobSpy sites
from resume_tailor.scrape_jobs import main
main()