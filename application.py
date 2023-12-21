from flask import Flask, request, jsonify
import pandas as pd
import math
import time

app = Flask(__name__)

# Load the CSV data
us_cities_csv_file_path = r'us-cities.csv'
df = pd.read_csv(us_cities_csv_file_path)

@app.route('/data/closest_cities', methods=['GET'])
def get_closest_cities():
    start_time = time.time()

    # 获取请求参数
    city = request.args.get('city', '')
    page_size = int(request.args.get('page_size', 50))
    page = int(request.args.get('page', 0))

    # 过滤出指定城市的数据
    city_data = df[df['city'] == city]

    # 检查城市是否存在
    if city_data.empty:
        return jsonify({"error": "City not found"})

    # 获取城市坐标
    city_coords = (float(city_data['lat']), float(city_data['lng']))

    # 计算所有城市到给定城市的欧拉距离
    df['eular_distance'] = df.apply(lambda row: math.sqrt((float(row['lat']) - city_coords[0])**2 + (float(row['lng']) - city_coords[1])**2), axis=1)

    # 按照欧拉距离升序排序
    sorted_data = df.sort_values(by='eular_distance')

    # 分页处理
    paginated_data = sorted_data.iloc[page * page_size:(page + 1) * page_size]

    # 构建返回的 JSON 数据
    result = {
        "cities": paginated_data.to_dict(orient='records'),
        "response_time": int((time.time() - start_time) * 1000)  # 计算响应时间（毫秒）
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)