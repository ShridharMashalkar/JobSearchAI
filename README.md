# Resume Tailor Pipeline 🚀

An automated, production-grade AI pipeline designed to read job descriptions (JDs), screen them against your profile, tailor your resume/CV and cover letter for maximum ATS optimization, compile them into beautiful PDF documents using LaTeX, and track applications in an Excel database.

The pipeline executes **three LLM calls** in sequence:
1. **Screening**: Analyzes the Job Description to extract the company name, job title, responsibilities, required technical/soft skills, and computes an overall fit/gap analysis.
2. **Resume Tailoring**: Customizes your experience, education, and skills based on the screening results to maximize ATS alignment.
3. **Cover Letter Generation**: Writes a personalized cover letter matching the job requirements and your background.

---

## 👁️ Visual Examples & Sample Documents

To see how the tailored documents look once compiled into PDFs:
- Explore the sample_docs directory.
- For example, sample_docs/risebird_data_scientist/ contains:
  - `John_Doe_CV.pdf`: The compiled PDF resume.
  - `John_Doe_CoverLetter.pdf`: The compiled PDF cover letter.
  - `AI_Analysis.txt`: The structured AI analysis from all the three LLM calls.
  - `jd.txt`: The source job description.

---

## 🛠️ Step-by-Step Setup & Installation

### 1. Prerequisites
- **Python 3.11+**
- **LaTeX Distribution** (with `pdflatex` available in your system path).
  - *Windows*: [MiKTeX](https://miktex.org/) is recommended.
  - *Setup Guide*: Check out this YouTube tutorial on setting up LaTeX: [Installing LaTeX in IDE](https://www.youtube.com/watch?v=4lyHIQl4VM8).

### 2. Install Astral `uv`
`uv` is an extremely fast Python package manager and dependency resolver.
- **Windows (PowerShell)**:
  ```powershell
  irm https://astral.sh/uv/install.ps1 | iex
  ```
- **Other / Alternative (pip)**:
  ```powershell
  pip install uv
  ```

### 3. Initialize & Install Dependencies
Navigate to the project root directory and sync the virtual environment:
```powershell
uv sync
```
This registers the virtual environment and installs the package with its CLI entry point (`resume-tailor`).

### 4. Set Up Environment Variables
Edit the `.env` file in the project root folder and specify your OpenAI API key:
```env
OPENAI_API_KEY=sk-proj-GH4ERHnNYv7v...[your api key]...vYMCA
```
To obtain a key, visit [OpenAI](https://platform.openai.com/api-keys).

---

## ⚙️ Configuration & Customization

The pipeline is configured across two main files:

### 1. Personal Resume Profile: `data/resume.yaml`
Modify data/resume.yaml to fill in your personal resume details.
- **Personal Details**: Name, contact details, LinkedIn URL, and professional headline.
- **Experience & Education**: Define roles, dates, descriptions, and the target bullet count limit (`TotalBulletPointsToInclude: 3`) for the writing model.
- **Dynamic Experience Customization**: Configured via the `totalExperienceInYears` field (e.g. `totalExperienceInYears: 4+` or `3.5`). This value is dynamically injected into the LLM constraint prompt, avoiding hardcoded values.
- **Additional Sections**: Projects, certifications, publications, languages, and hobbies.

### 2. Pipeline Settings: `config/pipeline_config.yaml`
Modify config/pipeline_config.yaml to customize system paths and execution preferences.
- **Paths**: Define folders for `jd_input_folder`, `output_folder`, and the `jobs_excel_path`.
- **Output Filenames**: Customize names for generated files (e.g., `John_Doe_CV.pdf`, `John_Doe_CoverLetter.pdf`, etc.).
- **Sections Inclusion Flags**: Enable or disable sections dynamically in the generated resume under the `data:` block:
  ```yaml
  data:
    include_projects: true
    include_certifications: true
    include_publications: true
  ```

---

## 🏃 How to Run the Pipeline

Ready to apply? Follow these simple execution steps:

1. **Scrape or Add Job Descriptions**: 
   - **Automated Scraping**: You can automatically scrape jobs from LinkedIn, Indeed or Apify by running the `run_scrape.py` script. **Make sure to edit the search parameters directly in the `run_scrape.py` Python file to affect the job scraping before running this**. If using Apify, Add the APIFY_API_KEY in the .env environment file.
     ```env
     APIFY_API_KEY=apify_api_...[your api key]...
     ``` 
     Target options are linkedin, indeed and apify
     ```powershell
     uv run python run_scrape.py --target linkedin
     ```
     ```powershell
     uv run python run_scrape.py --target apify
     ```
   
   - **Manual Addition**: Alternatively, save a target Job Description as a plain text file (`.txt`) directly in the **`jobs/input`** folder (e.g., `jobs/input/software_engineer.txt`).

2. **Activate the Virtual Environment**:
   ```powershell
   .\.venv\Scripts\activate.bat
   ```
3. **Execute Command**: Run the pipeline via `uv`:
   ```powershell
   uv run resume-tailor --config config/pipeline_config.yaml
   ```

---

## 📂 Output & Tracking

After a successful run, the following outputs are generated:

### 1. Tailored Application Documents (`output/` folder)
For every processed job, a dedicated folder (e.g., `output/companyname_jobtitle/`) is created containing:
- `John_Doe_CV.pdf` (or your customized resume filename)
- `John_Doe_CoverLetter.pdf` (or your customized cover letter filename)
- `AI_Analysis.txt` (structured JSON assessment of fit, keywords, etc.)
- `jd.txt` (a copy of the source Job Description)
- The raw source `.tex` markup files if you need to perform manual tweaks in LaTeX.

### 2. Application Tracker (`tracking/` folder)
- The tracking folder contains `jobs.xlsx` (an Excel workbook/database), which automatically appends a new row with the processed job details, company name, fit score, and missing keywords.
- **Restructured Excel Columns**: The tracker follows a strict column sequence with clean, properly capitalized headers and standardized formatting:
  1. `Company`
  2. `Title`
  3. `Overall Fit`
  4. `Date` (always formatted as `DD-MM-YYYY`, e.g. `04-06-2026`)
  5. `Application Status`
  6. `Job URL`
  7. `Role Summary`
  8. `Key Responsibilities`
  9. `Technical Skills`
  10. `Soft Skills`
  11. `Missing Keywords`
  12. `Output Folder`
- Missing fields remain empty (null/blank) rather than shifting columns.

### 3. Application Visualization Dashboard (`dashboard.html`)
- To visualize your entire job search progress in a premium dashboard, run the command mentioned below:

```
uv run python server.py
```

Open the link mentioned in the command terminal after the server starts.
Visualize the dashboard, along with capabilities of Database Update and Refresh buttons.
It currently has mock data. To show real data once you start applying delete the tracking/jobs.xlsx file. The code will automatically create new file and keep appending new data.


### 4. Additional Features
Cleaning Output folder to remove rejected resumes, run below command:
Use this command after updating the excel sheet via the dashboard and setting the job application status to rejected.

```
python -m resume_tailor.cleanup
```

This will move all the rejected resumes from output folder to rejected_resumes folder.

---

## ⚙️ Configurations

The `config/pipeline_config.yaml` file controls the entire pipeline behavior, including file paths, model settings, and which sections to include in the generated resume.

### Paths
- **`jd_input_folder`**: Directory where raw job description text files are placed.
- **`output_folder`**: Directory where the tailored documents and analysis are saved.
- **`error_folder`**: Directory for jobs that failed to process.
- **`work_root`**: Temporary working directory.
- **`resume_yaml_path`**: Path to your personal resume data.
- **`resume_template_path`**: Path to the LaTeX CV template.
- **`cover_letter_template_path`**: Path to the LaTeX Cover Letter template.
- **`jobs_excel_path`**: Path to the Excel tracking database.

### Filenames
- **`analysis_filename`**: Name of the AI analysis output file.
- **`jd_filename`**: Name of the copied JD file.
- **`resume_tex_filename` / `cover_letter_tex_filename`**: Names of the intermediate LaTeX source files.
- **`resume_pdf_filename` / `cover_letter_pdf_filename`**: Names of the final compiled PDF outputs.
- **`error_jd_suffix`**: Suffix appended to failed job descriptions.

### LLM Settings
- **`model_name`**: The OpenAI model used for processing (e.g., `gpt-5.4-mini`).
- **`temperature`**: Creativity index (0.2 recommended for consistent, factual extraction).
- **`max_retries`**: Number of times the pipeline will retry a failed LLM call.
- **`request_timeout_seconds`**: Timeout duration for API calls.

### Data Flags
These configurations control the LLM prompts and the sections included in your generated resume:
- **`send_missing_keywords`**: Sends missing keywords to the resume tailoring prompt (second LLM call) to better align with the job description.
- **`send_current_resume`**: Sends your original complete resume to the second LLM call. If `false`, it does not send the whole YAML file, but just sends your company and job titles as a rough overall summary.
- **`send_raw_jd`**: Sends the raw job description to the second (resume) and third (cover letter) LLM calls.
- **`include_projects`**: Enables or disables the inclusion of projects in the generated resume.
- **`include_certifications`**: Enables or disables the inclusion of certifications in the generated resume.
- **`include_publications`**: Enables or disables the inclusion of publications in the generated resume.
