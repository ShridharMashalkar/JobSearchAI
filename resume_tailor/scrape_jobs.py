"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from jobspy import scrape_jobs

from resume_tailor.config import load_config
from resume_tailor.files import ensure_directory, slugify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape jobs using JobSpy and save them to the input folder.")
    parser.add_argument("--term", type=str, required=False, help="Job search term (e.g. 'Software Engineer')")
    parser.add_argument("--google-term", type=str, required=False, help="Specific search term for Google jobs")
    parser.add_argument("--location", type=str, default="", help="Job location (e.g. 'San Francisco, CA')")
    parser.add_argument("--distance", type=int, default=50, help="Distance in miles")
    parser.add_argument("--job-type", type=str, choices=["fulltime", "parttime", "internship", "contract"], help="Type of job")
    parser.add_argument("--remote", action="store_true", help="Filter for remote jobs")
    parser.add_argument("--results", type=int, default=10, help="Number of results to fetch per platform")
    parser.add_argument("--hours-old", type=int, help="Only fetch jobs posted in the last N hours")
    parser.add_argument("--sites", type=str, default="linkedin,indeed,glassdoor", help="Comma-separated list of sites (linkedin,indeed,glassdoor,google,zip_recruiter)")
    parser.add_argument("--country", type=str, default="USA", help="Country for Indeed/Glassdoor (e.g. Germany)")
    parser.add_argument("--offset", type=int, default=0, help="Offset for pagination")
    parser.add_argument("--easy-apply", action="store_true", help="Filter for easy apply")
    parser.add_argument("--linkedin-fetch-description", action="store_true", help="Fetch full descriptions from LinkedIn (slower)")
    parser.add_argument("--config", type=str, default="config/pipeline_config.yaml", help="Path to config file")

    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        LOGGER.error(f"Config file not found at {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    input_folder = ensure_directory(config.paths.jd_input_folder)

    sites_list = [s.strip() for s in args.sites.split(",") if s.strip()]

    LOGGER.info(f"Scraping {args.results} jobs from {sites_list} for '{args.term}' in '{args.location}'")
    
    # Build arguments dict avoiding Nones for optional params
    scrape_args = {
        "site_name": sites_list,
        "location": args.location,
        "distance": args.distance,
        "results_wanted": args.results,
        "country_indeed": args.country,
        "offset": args.offset,
        "is_remote": args.remote,
        "easy_apply": args.easy_apply,
        "linkedin_fetch_description": args.linkedin_fetch_description,
    }

    if args.term:
        scrape_args["search_term"] = args.term
    if args.google_term:
        scrape_args["google_search_term"] = args.google_term
    if args.job_type:
        scrape_args["job_type"] = args.job_type
    if args.hours_old:
        scrape_args["hours_old"] = args.hours_old

    try:
        jobs = scrape_jobs(**scrape_args)
    except Exception as e:
        LOGGER.error(f"Error scraping jobs: {e}")
        sys.exit(1)

    if jobs.empty:
        LOGGER.info("No jobs found matching the criteria.")
        return

    LOGGER.info(f"Found {len(jobs)} jobs. Saving to {input_folder}...")

    saved_count = 0
    for _, row in jobs.iterrows():
        description = row.get("description", "")
        # JobSpy might return NaN for missing descriptions
        if not description or str(description) == "nan":
            company = str(row.get("company", "Unknown"))
            title = str(row.get("title", "Job"))
            LOGGER.warning(f"Skipping {title} at {company} because description is missing.")
            continue

        company = str(row.get("company", "Unknown"))
        title = str(row.get("title", "Job"))
        job_url = str(row.get("job_url", ""))
        
        # Create a safe filename
        safe_company = slugify(company, separator="_")
        safe_title = slugify(title, separator="_")
        job_id = str(row.get("id", "0"))
        
        filename = f"{safe_company}_{safe_title}_{job_id}.txt"
        file_path = input_folder / filename

        # Write text
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\n")
            f.write(f"Company: {company}\n")
            f.write(f"URL: {job_url}\n")
            f.write("\n--- Description ---\n\n")
            f.write(str(description))
            
        saved_count += 1

    LOGGER.info(f"Successfully saved {saved_count} job descriptions to {input_folder}")

if __name__ == "__main__":
    main()
