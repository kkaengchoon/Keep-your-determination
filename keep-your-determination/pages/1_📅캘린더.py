import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from datetime import datetime, date, time
import streamlit.components.v1 as components
import os
import json
import google.auth.transport.requests

# 자격 증명 파일 이름
CREDENTIALS_FILE = "google_credentials.json"

# Streamlit 설정
st.set_page_config(page_title="Calendar", page_icon="📅", layout="centered")
st.title("📅 스케줄 관리 페이지")

# 자격 증명 관련 함수
def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
    }

def save_credentials_to_file(creds):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds_to_dict(creds), f)

def load_credentials_from_file():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds_dict = json.load(f)
            creds = google.oauth2.credentials.Credentials(**creds_dict)
            return creds
    return None

def refresh_credentials(creds):
    if creds and creds.expired and creds.refresh_token:
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        save_credentials_to_file(creds)
    return creds

def logout():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)
        st.success("성공적으로 로그아웃되었습니다.")
        st.experimental_rerun()

def login():
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",  # 반드시 유효한 경로로 수정
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        creds = flow.run_local_server(port=0)
        save_credentials_to_file(creds)
        return creds
    except FileNotFoundError:
        st.error("클라이언트 비밀키 파일(client_secret.json)을 찾을 수 없습니다. 경로를 확인하세요.")
    except Exception as e:
        st.error(f"로그인 중 오류 발생: {e}")
    return None

# 캘린더 일정 관련 함수
def add_event(service, summary, location, description, start_time, end_time, time_zone='Asia/Seoul'):
    try:
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': time_zone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': time_zone,
            },
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event
    except Exception as e:
        st.error(f"일정 추가 중 오류 발생: {e}")

def fetch_events(service):
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        return events_result.get('items', [])
    except Exception as e:
        st.error(f"이벤트를 가져오는 중 오류 발생: {e}")
        return []

def render_fullcalendar(events, calendar_height=600):
    try:
        events_json = [{'title': event['summary'], 'start': event['start'].get('dateTime', event['start'].get('date'))} for event in events]
        calendar_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.9.0/main.min.css' rel='stylesheet' />
          <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.9.0/main.min.js'></script>
          <script>
            document.addEventListener('DOMContentLoaded', function() {{
              var calendarEl = document.getElementById('calendar');
              var calendar = new FullCalendar.Calendar(calendarEl, {{
                initialView: 'dayGridMonth',
                events: {events_json}
              }});
              calendar.render();
            }});
          </script>
        </head>
        <body>
          <div id='calendar'></div>
        </body>
        </html>
        """
        components.html(calendar_html, height=calendar_height)
    except Exception as e:
        st.error(f"캘린더 렌더링 중 오류 발생: {e}")

# 로그인 상태 확인
creds = load_credentials_from_file()
if creds:
    creds = refresh_credentials(creds)
    service = build('calendar', 'v3', credentials=creds)
    st.success("로그인 상태가 유지되었습니다.")
    if st.button("로그아웃"):
        logout()
else:
    if st.button("로그인"):
        creds = login()
        if creds:
            service = build('calendar', 'v3', credentials=creds)

# 캘린더 일정 렌더링
if creds:
    events = fetch_events(service)
    if events:
        render_fullcalendar(events)
    else:
        st.warning("표시할 이벤트가 없습니다.")

# 일정 추가 UI
if creds:
    with st.expander("새로운 일정 추가"):
        event_summary = st.text_input("일정 제목", "")
        event_location = st.text_input("일정 장소", "")
        event_description = st.text_area("일정 설명", "")

        start_date = st.date_input("시작 날짜", value=date.today())
        start_time_str = st.text_input("시작 시간 (HH:MM)", value=datetime.now().strftime("%H:%M"))
        end_date = st.date_input("종료 날짜", value=date.today())
        end_time_str = st.text_input("종료 시간 (HH:MM)", value=(datetime.now().replace(hour=(datetime.now().hour + 1))).strftime("%H:%M"))

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)

            if st.button("일정 추가"):
                created_event = add_event(service, event_summary, event_location, event_description, start_datetime, end_datetime)
                if created_event:
                    st.success("일정이 성공적으로 추가되었습니다.")
                    events = fetch_events(service)
                    render_fullcalendar(events)
        except ValueError:
            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요.")