import json
import os
import streamlit as st
from datetime import datetime, date, time as dt_time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import requests
import time

# Streamlit 설정
st.set_page_config(page_title="캘린더", page_icon="\ud83d\udcc5", layout="centered")
st.title("\ud83d\udcc5 Google Calendar 관리")

# 상태 기반 새로고침 함수
def rerun():
    st.session_state["force_rerun"] = time.time()  # 상태 변경 유도

def clear_all_session_keys():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Google Client Secret 파일 생성
def create_client_secret_file():
    client_secret_content = st.secrets["google"]["client_secret"]
    client_secret_path = "client_secret.json"
    with open(client_secret_path, "w") as f:
        f.write(client_secret_content)
    return client_secret_path

# Google Credentials 파일 생성
def create_credentials_file():
    credentials_content = st.secrets["google"]["credentials"]
    credentials_path = "google_credentials.json"
    with open(credentials_path, "w") as f:
        f.write(credentials_content)
    return credentials_path

# 동적으로 파일 생성
CLIENT_SECRET_FILE = create_client_secret_file()
CREDENTIALS_FILE = create_credentials_file()

# 자격 증명 관련 함수
def load_credentials_from_file():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds_dict = json.load(f)
            return Credentials(**creds_dict)
    return None

def save_credentials_to_file(creds):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
        }, f)

def refresh_credentials(creds):
    if creds and creds.expired and creds.refresh_token:
        request = Request()
        creds.refresh(request)
        save_credentials_to_file(creds)
    return creds

# Google Calendar API 서비스 생성
def create_service():
    creds = refresh_credentials(st.session_state["credentials"])
    return build("calendar", "v3", credentials=creds)

# 로그인 함수
def login():
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        auth_url, _ = flow.authorization_url(prompt="select_account")  # 계정 선택 강제
        st.write(f"[인증 URL을 클릭하세요]({auth_url})")
        auth_code = st.text_input("인증 코드를 입력하세요:")
        if auth_code:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            st.session_state["credentials"] = creds
            save_credentials_to_file(creds)
            rerun()  # 페이지 새로고침
    except Exception as e:
        st.error(f"로그인 중 오류 발생: {e}")

# Google OAuth 토큰 무효화
def revoke_token():
    if "credentials" in st.session_state:
        creds = st.session_state["credentials"]
        revoke_url = f"https://oauth2.googleapis.com/revoke?token={creds.token}"
        response = requests.post(revoke_url)
        if response.status_code == 200:
            st.success("토큰이 성공적으로 무효화되었습니다.")
        else:
            st.error("토큰 무효화 중 오류가 발생했습니다.")

# 로그아웃 함수
def logout():
    try:
        clear_all_session_keys()
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)
        revoke_token()  # 토큰 무효화
        st.success("성공적으로 로그아웃되었습니다. 브라우저에서 Google 계정을 로그아웃하려면 아래 링크를 클릭하세요.")
        st.markdown("[Google 로그아웃하기](https://accounts.google.com/Logout)")
        rerun()
    except Exception as e:
        st.error(f"로그아웃 중 오류 발생: {e}")

# 캘린더 일정 관련 함수
def fetch_events(service):
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        st.error(f"이벤트를 가져오는 중 오류 발생: {e}")
        return []

def add_event(service, summary, start_datetime, end_datetime, time_zone='Asia/Seoul'):
    try:
        event = {
            'summary': summary,
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': time_zone},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': time_zone},
        }
        service.events().insert(calendarId='primary', body=event).execute()
        st.success("일정이 추가되었습니다.")
    except Exception as e:
        st.error(f"일정 추가 중 오류 발생: {e}")

def update_event(service, event_id, summary, start_datetime, end_datetime, time_zone='Asia/Seoul'):
    try:
        event = {
            'summary': summary,
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': time_zone},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': time_zone},
        }
        service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        st.success("일정이 수정되었습니다.")
    except Exception as e:
        st.error(f"일정 수정 중 오류 발생: {e}")

def delete_event(service, event_id):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        st.success("일정이 삭제되었습니다.")
    except Exception as e:
        st.error(f"일정 삭제 중 오류 발생: {e}")

# 로그인 상태 초기화
if "credentials" not in st.session_state:
    st.session_state["credentials"] = load_credentials_from_file()

# 로그인 상태에 따른 UI 렌더링
if st.session_state["credentials"]:
    service = create_service()
    st.success("로그인 상태 유지 중")
    if st.button("로그아웃"):
        logout()

    # 캘린더 관리 UI
    events = fetch_events(service)
    st.header("일정 관리")

    # 새 일정 추가
    with st.expander("새 일정 추가"):
        summary = st.text_input("일정 제목", key="add_summary")
        start_date = st.date_input("시작 날짜", value=date.today(), key="add_start_date")
        start_time = st.text_input("시작 시간 (HH:MM)", "09:00", key="add_start_time")
        end_date = st.date_input("종료 날짜", value=date.today(), key="add_end_date")
        end_time = st.text_input("종료 시간 (HH:MM)", "10:00", key="add_end_time")
        if st.button("일정 추가"):
            try:
                start_datetime = datetime.combine(start_date, datetime.strptime(start_time, "%H:%M").time())
                end_datetime = datetime.combine(end_date, datetime.strptime(end_time, "%H:%M").time())
                add_event(service, summary, start_datetime, end_datetime)
            except Exception as e:
                st.error(f"일정 추가 중 오류 발생: {e}")

    # 기존 일정 수정
    with st.expander("기존 일정 수정"):
        if events:
            selected_event = st.selectbox(
                "수정할 이벤트 선택",
                events,
                format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음',
                key="edit_event_select"
            )
            if selected_event:
                new_title = st.text_input("새로운 제목", selected_event['summary'], key="edit_summary")
                new_start_date = st.date_input("새로운 시작 날짜", value=datetime.fromisoformat(selected_event['start'].get('dateTime', selected_event['start'].get('date'))).date(), key="edit_start_date")
                new_start_time = st.text_input("새로운 시작 시간 (HH:MM)", "09:00", key="edit_start_time")
                new_end_date = st.date_input("새로운 종료 날짜", value=datetime.fromisoformat(selected_event['end'].get('dateTime', selected_event['end'].get('date'))).date(), key="edit_end_date")
                new_end_time = st.text_input("새로운 종료 시간 (HH:MM)", "10:00", key="edit_end_time")

                if st.button("일정 수정"):
                    try:
                        event_id = selected_event["id"]
                        new_start_datetime = datetime.combine(new_start_date, datetime.strptime(new_start_time, "%H:%M").time())
                        new_end_datetime = datetime.combine(new_end_date, datetime.strptime(new_end_time, "%H:%M").time())
                        update_event(service, event_id, new_title, new_start_datetime, new_end_datetime)
                    except Exception as e:
                        st.error(f"일정 수정 중 오류 발생: {e}")
        else:
            st.warning("수정 가능한 일정이 없습니다.")

    # 기존 일정 삭제
    with st.expander("기존 일정 삭제"):
        if events:
            selected_event = st.selectbox(
                "삭제할 이벤트 선택",
                events,
                format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음',
                key="delete_event_select"
            )
            if st.button("이벤트 삭제"):
                try:
                    delete_event(service, selected_event['id'])
                except Exception as e:
                    st.error(f"일정 삭제 중 오류 발생: {e}")
        else:
            st.warning("삭제 가능한 일정이 없습니다.")
else:
    st.warning("로그인이 필요합니다.")
    if st.button("로그인"):
        login()
