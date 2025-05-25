import requests

TOKEN = 'y0__xC6m768Bxij8Dcg0KzNmBPGCV_m6dNujpdHUgbOV0_m4ne36A'
COUNTER_ID = '96743920'

headers = {
    'Authorization': f'OAuth {TOKEN}'
}

params = {
    'metrics': 'ym:s:visits,ym:s:pageviews,ym:s:users',
    'dimensions': 'ym:s:lastTrafficSource',
    'date1': '7daysAgo',
    'date2': 'today',
    'ids': COUNTER_ID,
    'limit': 100
}

response = requests.get(
    'https://api-metrika.yandex.net/stat/v1/data',
    headers=headers,
    params=params
)

data = response.json()
print(data)
