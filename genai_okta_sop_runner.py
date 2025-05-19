
import os
import time
import csv
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

okta_domain = os.getenv("OKTA_DOMAIN")
api_token = os.getenv("OKTA_API_TOKEN")

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

sops = {
    "1": "Reset password",
    "2": "Deactivate user",
    "3": "Suspend user (same as deactivate)",
    "4": "Reactivate user",
    "5": "Unlock user account",
    "6": "Reset MFA for user",
    "7": "Add user to group",
    "8": "Remove user from group",
    "9": "Create user and assign group",
    "10": "Assign Super Admin role",
    "11": "List user groups",
    "12": "Remove application access",
    "13": "Pull login history",
    "14": "Change department in profile"
}

def interpret_sop_with_genai(sop_text):
    messages = [
        {"role": "system", "content": "You are an Okta automation assistant. Your job is to interpret SOPs and recommend the API call and input required."},
        {"role": "user", "content": f"Here's an SOP: {sop_text}. Tell me the exact Okta API to use and what input is required."}
    ]
    response = client.chat.completions.create(
        model="gemma-2-2b-it",
        messages=messages
    )
    return response.choices[0].message.content

def get_headers():
    return {
        "Authorization": f"SSWS {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_user_id(email):
    url = f"{okta_domain}/api/v1/users?q={email}"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200 and res.json():
        return res.json()[0]["id"]
    return None

def get_group_id(name):
    url = f"{okta_domain}/api/v1/groups?q={name}"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200 and res.json():
        return res.json()[0]["id"]
    return None

def reset_password(user_id):
    return requests.post(f"{okta_domain}/api/v1/users/{user_id}/lifecycle/reset_password", headers=get_headers())

def deactivate_user(user_id):
    return requests.post(f"{okta_domain}/api/v1/users/{user_id}/lifecycle/deactivate", headers=get_headers())

def reactivate_user(user_id):
    return requests.post(f"{okta_domain}/api/v1/users/{user_id}/lifecycle/reactivate", headers=get_headers())

def unlock_user(user_id):
    return requests.post(f"{okta_domain}/api/v1/users/{user_id}/lifecycle/unlock", headers=get_headers())

def reset_mfa(user_id):
    return requests.delete(f"{okta_domain}/api/v1/users/{user_id}/factors", headers=get_headers())

def add_to_group(group_id, user_id):
    return requests.put(f"{okta_domain}/api/v1/groups/{group_id}/users/{user_id}", headers=get_headers())

def remove_from_group(group_id, user_id):
    return requests.delete(f"{okta_domain}/api/v1/groups/{group_id}/users/{user_id}", headers=get_headers())

def create_user(email, first_name, last_name):
    payload = {
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "login": email
        }
    }
    return requests.post(f"{okta_domain}/api/v1/users?activate=true", json=payload, headers=get_headers())

def assign_admin_role(user_id):
    payload = { "type": "SUPER_ADMIN" }
    return requests.post(f"{okta_domain}/api/v1/users/{user_id}/roles", json=payload, headers=get_headers())

def list_groups(user_id):
    return requests.get(f"{okta_domain}/api/v1/users/{user_id}/groups", headers=get_headers())

def pull_login_history(email):
    return requests.get(f"{okta_domain}/api/v1/logs?filter=target.name eq \"{email}\"", headers=get_headers())

def update_department(user_id, department):
    payload = { "profile": { "department": department } }
    return requests.post(f"{okta_domain}/api/v1/users/{user_id}", json=payload, headers=get_headers())

def process_csv(path):
    with open(path, newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            email = row['email']
            sop = row['sop_id']
            group = row.get('group', '')
            fname = row.get('firstName', '')
            lname = row.get('lastName', '')
            department = row.get('department', '')

            print(f"\n[INFO] Processing SOP {sop} for {email}")
            print(interpret_sop_with_genai(sops.get(sop, "Unknown SOP")))

            if sop == "9":
                response = create_user(email, fname, lname)
                print("[RESULT]", response.status_code, response.text)
                if response.ok and group:
                    user_id = response.json().get("id")
                    group_id = get_group_id(group)
                    if user_id and group_id:
                        add_to_group(group_id, user_id)
                continue

            user_id = get_user_id(email)
            if not user_id:
                print("[ERROR] User not found:", email)
                continue

            if sop == "1":
                print(reset_password(user_id).status_code)
            elif sop == "2" or sop == "3":
                print(deactivate_user(user_id).status_code)
            elif sop == "4":
                print(reactivate_user(user_id).status_code)
            elif sop == "5":
                print(unlock_user(user_id).status_code)
            elif sop == "6":
                print(reset_mfa(user_id).status_code)
            elif sop == "7":
                group_id = get_group_id(group)
                print(add_to_group(group_id, user_id).status_code)
            elif sop == "8":
                group_id = get_group_id(group)
                print(remove_from_group(group_id, user_id).status_code)
            elif sop == "10":
                print(assign_admin_role(user_id).status_code)
            elif sop == "11":
                response = list_groups(user_id)
                for g in response.json():
                    print(" -", g['profile']['name'])
            elif sop == "12":
                print("[SKIPPED] Remove app access - Not implemented")
            elif sop == "13":
                logs = pull_login_history(email)
                print("[LOGS]", logs.json()[:1])
            elif sop == "14":
                print(update_department(user_id, department).status_code)

if __name__ == "__main__":
    print("\n[START] Processing users from CSV...")
    process_csv("users.csv")
