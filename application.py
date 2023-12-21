from flask import Flask, request, jsonify
import pandas as pd
from sklearn.cluster import KMeans
import math
import time

app = Flask(__name__)

# Load the CSV data
us_cities_csv_file_path = r'us-cities.csv'
df = pd.read_csv(us_cities_csv_file_path)
cities_df = pd.read_csv('us-cities.csv')
reviews_df = pd.read_csv('amazon-reviews.csv')

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


# Endpoint to handle the KNN clustering request
@app.route('/data/knn_reviews', methods=['GET'])
def knn_reviews():
    try:
        # Get request parameters
        classes = int(request.args.get('classes'))
        k = int(request.args.get('k'))
        words = int(request.args.get('words'))

        # Extract relevant data for clustering
        X = cities_df[['lat', 'lng', 'population']]

        # Use KMeans for clustering
        kmeans = KMeans(n_clusters=classes, random_state=42)
        cities_df['cluster'] = kmeans.fit_predict(X)

        # Process clusters and prepare response
        results = []
        for cluster_id in range(classes):
            cluster_mask = (cities_df['cluster'] == cluster_id)
            cluster_cities = cities_df.loc[cluster_mask, 'city'].tolist()
            center_city = get_center_city(cluster_cities)
            popular_words = get_popular_words(cluster_cities, words)
            weighted_avg_score = calculate_weighted_avg_score(reviews_df, cluster_cities)

            result = {
                'class_id': cluster_id,
                'center_city': center_city,
                'cities': cluster_cities,
                'popular_words': popular_words,
                'weighted_avg_score': weighted_avg_score,
            }

            results.append(result)

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

def get_center_city(cities):
    # Replace this with your logic to determine the center city
    return cities[0] if cities else None

def get_popular_words(cities, num_words):
    # Replace this with your logic to determine popular words
    return ['i', 'the', 'me']  # Placeholder data


def calculate_weighted_avg_score(reviews_df, cluster_cities):
    # Merge reviews_df with cities_df to get the population information
    merged_df = pd.merge(reviews_df, cities_df[['city', 'population']], on='city', how='inner')

    # Filter for reviews of cities in the current cluster
    cluster_reviews = merged_df[merged_df['city'].isin(cluster_cities)]

    # Calculate weighted average score
    weighted_avg_score = (cluster_reviews['score'] * cluster_reviews['population']).sum() / cluster_reviews[
        'population'].sum()

    return weighted_avg_score

if __name__ == '__main__':
    app.run(debug=True)