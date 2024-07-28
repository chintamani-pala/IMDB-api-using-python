from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

def fetch_url_content(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        raise Exception(f"Request failed: {e}")

def extract_json_data(soup):
    script_tag = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
    if not script_tag:
        raise Exception("Script tag with id '__NEXT_DATA__' not found.")
    return json.loads(script_tag.string)

def search_by_name(name):
    url = f"https://m.imdb.com/find/?q={name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    soup = fetch_url_content(url, headers)
    data = extract_json_data(soup)
    return data.get("props", {}).get("pageProps", {}).get("titleResults", {}).get("results", [])

def extract_top_casts(page_props):
    top_casts = []
    cast_data = page_props.get("mainColumnData", {}).get("cast", {}).get("edges", [])
    for cast in cast_data:
        node = cast.get("node", {})
        characters = node.get("characters", [])
        name_data = node.get("name", {})
        primary_image = name_data.get("primaryImage", {})
        top_casts.append({
            "character_name": characters[0].get("name", "N/A") if characters else "N/A",
            "real_name": name_data.get("nameText", {}).get("text", "N/A"),
            "actor_image": primary_image.get("url", "N/A") if primary_image else "N/A"
        })
    return top_casts

def extract_common_details(page_props, fold_data):
    title_text = fold_data.get('originalTitleText', {}).get('text', 'N/A')
    thumbnail = fold_data.get('primaryImage', {}).get('url', 'N/A')
    release_year = fold_data.get("releaseDate", {}).get("year", "N/A")
    avg_rating = fold_data.get("ratingsSummary", {})
    avg_rating = "N/A" if avg_rating is None else avg_rating.get("aggregateRating", "N/A")
    rating_vote_count = fold_data.get("ratingsSummary", {})
    rating_vote_count = "N/A" if rating_vote_count is None else rating_vote_count.get("voteCount", "N/A")
    time_duration_data = fold_data.get("runtime")
    time_duration = "N/A" if time_duration_data is None else time_duration_data.get("displayableProperty", {}).get("value", {}).get("plainText", "N/A")
    # description = fold_data.get("plot", {}).get("plotText", {}).get("plainText", "No description available")
    plot_data = fold_data.get("plot", {})
    plot_text_data = plot_data.get("plotText",None) if plot_data else None
    description = "No description available" if plot_text_data is None else plot_text_data.get("plainText", "No description available")
    release_date = f'{fold_data.get("releaseDate", {}).get("day", "N/A")}/{fold_data.get("releaseDate", {}).get("month", "N/A")}/{fold_data.get("releaseDate", {}).get("year", "N/A")}'
    country_of_origin = page_props.get("mainColumnData", {}).get("countriesOfOrigin", {}).get("countries", [{}])[0].get("text", "N/A")
    spoken_languages_data = page_props.get("mainColumnData", {}).get("spokenLanguages")
    languages_list = spoken_languages_data.get("spokenLanguages") if spoken_languages_data else []
    languages = ', '.join([lang.get("text", "N/A") for lang in languages_list])
    
    isSeries = fold_data.get("titleType", {}).get("isSeries", "N/A")
    budget_data = page_props.get("mainColumnData", {}).get("productionBudget", {})
    
    budget_data = budget_data.get("budget", {}) if budget_data else {}
    production_budget = {
        "production_budget_price": budget_data.get("amount", "N/A"),
        "production_budget_currency": budget_data.get("currency", "N/A")
    }
    
    
    worldwide_gross_total_data = page_props.get("mainColumnData", {}).get("worldwideGross", {})
    worldwide_gross_total_data = worldwide_gross_total_data.get("total", {}) if worldwide_gross_total_data else {}
    worldwide_gross = {
        "worldwide_gross_amount": worldwide_gross_total_data.get("amount", "N/A"),
        "worldwide_gross_currency": worldwide_gross_total_data.get("currency", "N/A")
    }
    
    return {
        'titleText': title_text,
        'thumbnail': thumbnail,
        'releaseYear': release_year,
        'avgRating': avg_rating,
        'isSeries': isSeries,
        'ratingVoteCount': rating_vote_count,
        'timeDuration': time_duration,
        'description': description,
        'releaseDate': release_date,
        'countryOfOrigin': country_of_origin,
        'languages': languages,
        'productionBudget': production_budget,
        'worldwideGross': worldwide_gross,
        'topCasts': extract_top_casts(page_props)
    }

def extract_movie_details(page_props, fold_data, imdb_id):
    details = extract_common_details(page_props, fold_data)
    director = (
        fold_data.get("principalCredits", [{}])[0] if len(fold_data.get("principalCredits", [])) > 0 else "N/A")
    director = director.get("credits", [{}])[0] if len(director.get("credits", [])) > 0 else "N/A"
    director = (director.get("name", {}).get("nameText", {}).get("text", "N/A")
        if len(fold_data.get("principalCredits", [])) > 0 and
        len(fold_data.get("principalCredits", [{}])[0].get("credits", [])) > 0
        else "N/A")
    writer = (
        ', '.join([
            credit.get("name", {}).get("nameText", {}).get("text", "N/A")
            for credit in fold_data.get("principalCredits", [{}])[1].get("credits", [])
        ])
        if len(fold_data.get("principalCredits", [])) > 1
        else "N/A"
    )

    stars = (
        ', '.join([
            credit.get("name", {}).get("nameText", {}).get("text", "N/A")
            for credit in fold_data.get("principalCredits", [{}])[2].get("credits", [])
        ])
        if len(fold_data.get("principalCredits", [])) > 2
        else "N/A"
    )

    playbackURL = (
        fold_data.get("primaryVideos", {}).get("edges", [{}])[0]
        .get("node", {}).get("playbackURLs", [{}])[0]
        .get("url", "N/A")
        if len(fold_data.get("primaryVideos", {}).get("edges", [])) > 0 and
        len(fold_data.get("primaryVideos", {}).get("edges", [{}])[0]
        .get("node", {}).get("playbackURLs", [])) > 0
        else "N/A"
    )

    details.update({
        'imdb_id': imdb_id,
        'director': director,
        'writer': writer,
        'stars': stars,
        'playbackURL': playbackURL
    })
    
    return details
def extract_series_details(page_props, fold_data, imdb_id):
    details = extract_common_details(page_props, fold_data)

    director = (fold_data.get("principalCredits", [{}])[0].get("credits", [{}])[0].get("name", {}).get("nameText", {}).get("text", "N/A")
            if len(fold_data.get("principalCredits", [])) > 0 and len(fold_data.get("principalCredits", [{}])[0].get("credits", [])) > 0 else "N/A")

    creators = (', '.join([credit.get("name", {}).get("nameText", {}).get("text", "N/A") 
                       for credit in fold_data.get("principalCredits", [])[0].get("credits", [])]) 
            if len(fold_data.get("principalCredits", [])) > 0 else "N/A")

    stars = (', '.join([credit.get("name", {}).get("nameText", {}).get("text", "N/A") 
                    for credit in fold_data.get("principalCredits", [])[1].get("credits", [])]) 
         if len(fold_data.get("principalCredits", [])) > 1 else "N/A")

    playbackURL = (fold_data.get("primaryVideos", {}).get("edges", [{}])[0].get("node", {}).get("playbackURLs", [{}])[0].get("url", "N/A")
               if len(fold_data.get("primaryVideos", {}).get("edges", [])) > 0 and 
               len(fold_data.get("primaryVideos", {}).get("edges", [{}])[0].get("node", {}).get("playbackURLs", [])) > 0 else "N/A")

    details.update({
        'imdb_id': imdb_id,
        'director': director,
        'creators': creators,
        'stars': stars,
        'playbackURL': playbackURL
    })
    return details

def extract_data(imdb_id):
    url = f"https://m.imdb.com/title/{imdb_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    
    soup = fetch_url_content(url, headers)
    data = extract_json_data(soup)
    page_props = data.get('props', {}).get('pageProps', {})
    fold_data = page_props.get('aboveTheFoldData', {})
    
    if fold_data.get("titleType", {}).get("isSeries", False):
        return extract_series_details(page_props, fold_data, imdb_id)
    else:
        return extract_movie_details(page_props, fold_data, imdb_id)

@app.route('/', methods=['GET'])
def index():
    return jsonify({'credits': 'Made with ❤️ by Chintamani Pala', "version": "1.0.0", "website": "https://chintamanipala.in"})

@app.route('/api/search', methods=['GET'])
def search_movie():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        results = search_by_name(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/search/getFullInfo", methods=['GET'])
def get_full_info():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        results = search_by_name(query)
        ids = [result['id'] for result in results]
        fullInfo = []

        for id in ids:
            try:
                full_info = extract_data(id)
                fullInfo.append(full_info)
            except Exception as e:
                print(f"Failed to extract data for ID {id}: {e}")  
                continue

        return jsonify(fullInfo)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/movie', methods=['GET'])
def get_movie_data():
    imdb_id = request.args.get('id')
    if not imdb_id:
        return jsonify({'error': 'IMDb ID is required'}), 400

    try:
        extracted_data = extract_data(imdb_id)
        return jsonify(extracted_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
