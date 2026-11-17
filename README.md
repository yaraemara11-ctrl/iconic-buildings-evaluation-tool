# Iconic Buildings Evaluation Tool

A Streamlit prototype implementing the supplied binary evaluation model.

## Run locally
1. Install Python 3.10 or later.
2. Open a terminal in this folder.
3. Run: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`

## Publish online
Push this folder to a GitHub repository, then create a Streamlit Community Cloud app
pointing to `app.py`. The app will provide a shareable URL.

## Model implemented
- Core requirements: Iconic Vision (IV), Novelty (N), Applicability (A).
- All three core requirements must be achieved.
- If any core requirement is not achieved: Not Qualified.
- If core requirements pass, classify by the number of achieved complementary outcomes:
  4 = Q1, 3 = Q2, 2 = Q3, 1 = Q4, 0 = Q5.
- No numerical scoring or weighting is applied.
