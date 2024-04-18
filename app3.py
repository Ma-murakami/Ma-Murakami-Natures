import streamlit as st
import openai
import googlemaps
import pandas as pd
import requests
from datetime import datetime, timedelta

# APIキー設定
GMAPS_API_KEY = 'AIzaSyDgquYvkDL3AD1zUBlqAKDMuoZzgwo3qDI'
OPENAI_API_KEY = 'sk-proj-cUlxEMlyvWosujHDgib1T3BlbkFJfCgiLk7bAs6MCJyyTJ7m'
WEATHER_API_KEY = 'bfa5ee7d3df2b9762e805c0d95ea64c8'

# APIクライアントの初期化
gmaps = googlemaps.Client(key=GMAPS_API_KEY)
openai.api_key = OPENAI_API_KEY

# 都道府県リスト（北海道と山形県のみ）
prefectures = ["北海道", "山形県"]

# 旅の目的のリスト
travel_purposes = ["一人旅", "家族連れでの旅行", "アウトドアを楽しむための旅行", "サウナ巡り"]

# Streamlitアプリ
def main():
    st.title('観光地選択とルート案内')
    # ユーザー入力
    area_query = st.selectbox('都道府県を選択してください', prefectures)
    travel_purpose = st.selectbox('旅の目的を選択してください', travel_purposes)
    number_of_sites = st.slider('表示する観光地の数', 1, 5, 3)
    # Session state initialization
    if 'descriptions' not in st.session_state:
        st.session_state['descriptions'] = []
    if 'sites' not in st.session_state:
        st.session_state['sites'] = []
    show_details = st.button('詳細を表示')
    if show_details:
        # 観光地の候補と説明を取得
        prompt = f"あなたはプロフェッショナルなツアーガイドです。{travel_purpose}向けに{area_query}で訪れるべき{number_of_sites}つの観光地とそれぞれの説明を200文字以内で教えてください。"
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a professional tour guide."},
                      {"role": "user", "content": prompt}]
        )
        st.session_state['descriptions'] = response.choices[0].message['content'].split('\n')
        st.session_state['sites'] = [desc.split('：')[0].strip() for desc in st.session_state['descriptions'] if '：' in desc and desc.split('：')[0].strip()]
    if st.session_state['descriptions']:
        for desc in st.session_state['descriptions']:
            st.write(desc)

    chosen_sites = st.multiselect('行きたい観光地を選択してください', options=st.session_state['sites'])
    
    # 以下のコードはそのまま続きます...

    
    if chosen_sites:
        # 出発時間の選択
        departure_time = st.time_input('出発時間を選択してください', value=datetime.now())
        
        # 選択された各観光地の地図と移動時間を表示
        previous_location = None
        for site in chosen_sites:
            loc_result = gmaps.geocode(site + ', ' + area_query)
            if loc_result:
                loc = loc_result[0]['geometry']['location']
                st.header(site)
                st.map(pd.DataFrame({'lat': [loc['lat']], 'lon': [loc['lng']]}), zoom=11)
                
                if previous_location:
                    # Calculate travel time between the previous and current site
                    travel_time_info = gmaps.directions(previous_location, site + ', ' + area_query, mode="driving")
                    travel_duration = travel_time_info[0]['legs'][0]['duration']['text']  # Duration as string
                    st.write(f"移動時間（車）: {travel_duration}")
                    
                previous_location = site + ', ' + area_query  # Update previous location
                
                # Fetch weather forecast
                weather_forecast = fetch_weather_forecast(loc['lat'], loc['lng'])
                if weather_forecast:
                    st.subheader('天気予報')
                    st.write(weather_forecast)
                
        # プランの生成
        if st.button('プランを生成'):
            current_time = datetime.combine(datetime.today(), departure_time)
            previous_location = None
            for index, site in enumerate(chosen_sites):
                if previous_location:
                    # Calculate travel time between the previous and current site
                    travel_time_info = gmaps.directions(previous_location, site + ', ' + area_query, mode="driving")
                    travel_duration = travel_time_info[0]['legs'][0]['duration']['value']  # Duration in seconds
                    current_time += timedelta(seconds=travel_duration)
                    st.write(f"移動時間: {timedelta(seconds=travel_duration)}")
                st.write(f"{current_time.strftime('%H:%M')} - {site} (観光時間: 1時間)")
                current_time += timedelta(hours=1)  # 滞在時間
                previous_location = site + ', ' + area_query  # Update previous location

def fetch_weather_forecast(latitude, longitude):
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={latitude}&lon={longitude}&exclude=minutely,hourly&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        forecast_data = response.json()
        forecast = []
        for day in forecast_data['current']:
            date = datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d')
            weather_description = day['weather'][0]['description']
            max_temp = day['temp']['max']
            min_temp = day['temp']['min']
            forecast.append(f"{date}: {weather_description}, 最高気温: {max_temp}℃, 最低気温: {min_temp}℃")
        return forecast
    else:
        st.error("天気予報の取得に失敗しました。")
        return None

if __name__ == "__main__":
    main()



