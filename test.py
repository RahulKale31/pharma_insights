import requests

def test_clinical_trials_api():
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": "breast cancer",
        "pageSize": 100,
        "fields": "NCTId,BriefTitle,Condition,Phase,StartDate,CompletionDate,LeadSponsorName"  # Updated field names
    }
    
    headers = {
        "accept": "application/json"
    }
    
    print(f"Making request to: {base_url}")
    print(f"With parameters: {params}")
    
    response = requests.get(base_url, params=params, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print("\nHeaders:")
    print(response.headers)
    print("\nContent:")
    print(response.text[:1000])

if __name__ == "__main__":
    test_clinical_trials_api()