import streamlit as st
import pandas as pd
import pydeck as pdk
from urllib.error import URLError
import openai
import os
from datetime import datetime
import numpy as np

st.set_page_config(page_title="chatbot",
                   page_icon="https://cdn-icons-png.flaticon.com/128/14898/14898163.png",
                   layout="wide")

st.markdown("# chatbot")

