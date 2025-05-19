
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
okta_domain = os.getenv("OKTA_DOMAIN")
api_token = os.getenv("OKTA_API_TOKEN")

# Initialize GenAI client
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

def interpret_sop(sop_text):
    messages = [
        {"role": "system", "content": "You are an Okta automation assistant. Your job is to interpret SOPs and recommend the API call and input required."},
        {"role": "user", "content": f"Here's an SOP: {sop_text}. Tell me the exact Okta API to use and what input is required."}
    ]
    response = client.chat.completions.create(
        model="gemma-2-2b-it",
        messages=messages
    )
    return response.choices[0].message.content

def get_user_id(email):
    url = f"{okta_domain}/api/v1/users?q={email}"
    headers = {"Authorization": f"SSWS {api_token}", "Accept": "application/json"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return res.json()[0]["id"]
    return None

def reset_password(user_id):
    url = f"{okta_domain}/api/v1/users/{user_id}/lifecycle/reset_password"
    headers = {"Authorization": f"SSWS {api_token}", "Accept": "application/json", "Content-Type": "application/json"}
    return requests.post(url, headers=headers)

# Streamlit UI
st.title("GenAI + Okta Automation Portal")

sop_options = {
    "1 - Reset Password": "1",
    "2 - Deactivate User": "2",
    "3 - Suspend User": "3",
    "4 - Reactivate User": "4",
    "5 - Unlock User Account": "5",
    "6 - Reset MFA Factors": "6",
    "7 - Add to Group": "7",
    "8 - Remove from Group": "8",
    "9 - Create User & Assign Group": "9",
    "10 - Assign Admin Role": "10",
    "11 - List User Groups": "11",
    "12 - Remove App Access (stub)": "12",
    "13 - Pull Login History": "13",
    "14 - Update Department": "14"
}


sop_choice = st.selectbox("Choose SOP Action", list(sop_options.keys()))
email = st.text_input("User Email")

if st.button("Run SOP"):
    sop_id = sop_options[sop_choice]
    st.info(f"Interpreting SOP {sop_id} with GenAI...")
    interpretation = interpret_sop(f"{sop_choice.split('-')[1].strip()} for {email}")
    st.code(interpretation)

    user_id = get_user_id(email)
    if not user_id:
        st.error("User not found in Okta.")
    else:
        if sop_id == "1":
            response = reset_password(user_id)
            st.success(f"Password reset triggered: {response.status_code}")
        elif sop_id == "11":
            url = f"{okta_domain}/api/v1/users/{user_id}/groups"
            headers = {"Authorization": f"SSWS {api_token}", "Accept": "application/json"}
            response = requests.get(url, headers=headers)
            if response.ok:
                group_names = [g['profile']['name'] for g in response.json()]
                st.success("User is in the following groups:")
                st.write(group_names)
            else:
                st.error(f"Error fetching groups: {response.status_code}")
