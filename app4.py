import streamlit as st
import openai
import googlemaps
import pandas as pd
import requests
from datetime import datetime, timedelta

# APIキー設定
GMAPS_API_KEY = 'AIzaSyDgquYvkDL3AD1zUBlqAKDMuoZzgwo3qDI'
OPENAI_API_KEY = 'st.secrets[openai_APIkey]'
WEATHER_API_KEY = 'bfa5ee7d3df2b9762e805c0d95ea64c8'

# APIクライアントの初期化
gmaps = googlemaps.Client(key=GMAPS_API_KEY)
openai.api_key = OPENAI_API_KEY

# 都道府県リスト（例として北海道と山形県）
prefectures = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県","茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県","静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県","奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]

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
        descriptions = response.choices[0].message['content'].split('\n')
        sites = [desc.split('：')[0].strip() for desc in descriptions if '：' in desc and desc.split('：')[0].strip()]
        st.session_state['descriptions'] = descriptions
        st.session_state['sites'] = sites
        # 観光地の写真を表示
        for site in sites:
            loc_result = gmaps.geocode(site + ', ' + area_query)
            if loc_result:
                place_id = loc_result[0]['place_id']
                place_details = gmaps.place(place_id=place_id)
                if 'photos' in place_details['result']:
                    photo_reference = place_details['result']['photos'][0]['photo_reference']
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GMAPS_API_KEY}"
                    st.image(photo_url, caption=site)
                else:
                    st.write(f"{site}: 写真は利用できません。")
    if st.session_state['descriptions']:
        for desc in st.session_state['descriptions']:
            st.write(desc)

    chosen_sites = st.multiselect('行きたい観光地を選択してください', options=st.session_state['sites'])
    
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
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        weather_description = weather_data['weather'][0]['description']
        temp = weather_data['main']['temp']
        max_temp = weather_data['main']['temp_max']
        min_temp = weather_data['main']['temp_min']
        forecast = f"現在の天気: {weather_description}, 現在の気温: {temp}℃, 最高気温: {max_temp}℃, 最低気温: {min_temp}℃"
        return forecast
    else:
        st.error("天気予報の取得に失敗しました。")
        return None
if __name__ == "__main__":
    main()



