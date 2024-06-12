import pandas as pd
import streamlit as st
import base64
import os


def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def load_dataframe(name):
    df = pd.read_csv(name + '.csv')
    return df


class user_message:
    def __init__(self, text, user_name="You"):
        self.name = user_name
        self.container = st.empty()
        self.update(text)

    def update(self, text):
        message = f"""<div style='display:flex;align-items:center;justify-content:flex-end;margin-bottom:10px;'>
                     <div style='background-color:{st.get_option("theme.secondaryBackgroundColor")};border-radius:10px;padding:10px;'>
                     <p style='margin:0;font-weight:bold;'>{self.name}</p>
                     <p style='margin:0;color={st.get_option("theme.textColor")}'>{text}</p>
                     </div>
                     <img src='https://i.imgur.com/zDxXZKk.png' style='width:50px;height:50px;border-radius:50%;margin-left:10px;'>
                     </div>
        """
        self.container.write(message, unsafe_allow_html=True)
        return self


class bot_message:
    def __init__(self, text, bot_name="Assistant"):
        self.name = bot_name
        self.container = st.empty()
        self.update(text)

    def update(self, text):
        # Define the path to the logo image
        image_dir = "/app/img"
        image_logo = os.path.join(image_dir, "logo.png")

        # Convert the logo image to base64
        logo_base64 = get_image_base64(image_logo)

        message = f"""<div style='display:flex;align-items:center;margin-bottom:10px;'>
                    <img src='data:image/png;base64,{logo_base64}' style='width:50px;height:50px;border-radius:50%;margin-right:10px;'>
                    <div style='background-color:{st.get_option("theme.backgroundColor")};border: 1px solid {st.get_option("theme.secondaryBackgroundColor")};border-radius:10px;padding:10px;'>
                    <p style='margin:0;font-weight:bold;'>{self.name}</p>
                    <p style='margin:0;color:{st.get_option("theme.textColor")}'>{text}</p>
                    </div>
                    </div>
        """
        self.container.write(message, unsafe_allow_html=True)
        return self
