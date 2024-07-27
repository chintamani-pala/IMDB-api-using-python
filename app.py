from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)


def search_By_Name(name):
    url = f"https://m.imdb.com/find/?q={name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    script_tag = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
    if script_tag:
            json_content = script_tag.string
            data = json.loads(json_content)
    if data is None:
        return jsonify({"error": "Script tag with id '__NEXT_DATA__' not found."}), 404
    result=data.get("props",{}).get("pageProps",{}) if data else None
    if result is None:
        return jsonify({"error": "Script tag with id '__NEXT_DATA__' not found."}), 404
    result=result.get("titleResults",{}) if result else None
    if result is None:
        return jsonify({"error": "Script tag with id '__NEXT_DATA__' not found."}), 404
    result=result.get("results",[]) if result else None
    if result is None:
        return jsonify({"error": "Script tag with id '__NEXT_DATA__' not found."}), 404
    
    return result

def extract_top_casts(pageProps):
    top_casts = []
    cast_data = pageProps.get("mainColumnData", {}).get("cast", {})
    if cast_data is None:
        return top_casts
    
    top_casts_group = cast_data.get("edges", [])
    for i in top_casts_group:
        cast_obj = {}
        
        node = i.get("node", {})
        if node:
            characters = node.get("characters", [])
            cast_obj["character_name"] = characters[0].get("name", "N/A") if characters else "N/A"
            
            name_data = node.get("name", {})
            cast_obj["real_name"] = name_data.get("nameText", {}).get("text", "N/A")
            
            primary_image = name_data.get("primaryImage", {})
            cast_obj["actor_image"] = primary_image.get("url", "N/A") if primary_image else "N/A"
        else:
            cast_obj["character_name"] = "N/A"
            cast_obj["real_name"] = "N/A"
            cast_obj["actor_image"] = "N/A"
        
        top_casts.append(cast_obj)
    
    return top_casts
def extract_data(foldData, pageProps):
    try:
        title_text = foldData.get('originalTitleText', {}).get('text', 'N/A')
        thumbnail = foldData.get('primaryImage', {}).get('url', 'N/A')
        primary_video = foldData.get("primaryVideos", {}).get("edges", [{}])[0].get("node", {})
        release_year = primary_video.get("primaryTitle", {}).get("releaseYear", {}).get("year", "N/A")
        avg_rating = foldData.get("ratingsSummary", {}).get("aggregateRating", "N/A")
        rating_vote_count = foldData.get("ratingsSummary", {}).get("voteCount", "N/A")
        time_duration = foldData.get("runtime", {}).get("displayableProperty", {}).get("value", {}).get("plainText", "0h")
        description = foldData.get("plot", {}).get("plotText", {}).get("plainText", "No description available")
        director = foldData.get("principalCredits", [{}])[0].get("credits", [{}])[0].get("name", {}).get("nameText", {}).get("text", "N/A")
        
        writer = [i.get("name", {}).get("nameText", {}).get("text", "N/A") for i in foldData.get("principalCredits", [])[1].get("credits", [])]
        writer = ', '.join(writer)
        
        stars = [i.get("name", {}).get("nameText", {}).get("text", "N/A") for i in foldData.get("principalCredits", [])[2].get("credits", [])]
        stars = ', '.join(stars)
        
        playback_url = primary_video.get("playbackURLs", [{}])[0].get("url", "N/A")
        
        release_date = f'{foldData.get("releaseDate", {}).get("day", "N/A")}/{foldData.get("releaseDate", {}).get("month", "N/A")}/{foldData.get("releaseDate", {}).get("year", "N/A")}'
        
        country_of_origin = pageProps.get("mainColumnData", {}).get("countriesOfOrigin", {}).get("countries", [{}])[0].get("text", "N/A")
        
        languages = [i.get("text", "N/A") for i in pageProps.get("mainColumnData", {}).get("spokenLanguages", {}).get("spokenLanguages", [])]
        languages = ', '.join(languages)
        
        production_budget_data = pageProps.get("mainColumnData", {}).get("productionBudget", {})
        budget_data = production_budget_data.get("budget", {}) if production_budget_data else {}
        
        production_budget = {
            "production_budget_price": budget_data.get("amount", "N/A"),
            "production_budget_currency": budget_data.get("currency", "N/A")
        }
        worldwide_gross_data = pageProps.get("mainColumnData", {}).get("worldwideGross",{})
        worldwise_gross_total_data = worldwide_gross_data.get("total", {}) if worldwide_gross_data else {}
        worldwide_gross = {
            "worldwide_gross_amount" : worldwise_gross_total_data.get("amount","N/A") ,
            "worldwide_gross_currency" : worldwise_gross_total_data.get("currency","N/A") 
        }
        
        top_casts = extract_top_casts(pageProps)
        
        return {
            'titleText': title_text,
            'thumbnail': thumbnail,
            'releaseYear': release_year,
            'avgRating': avg_rating,
            'ratingVoteCount': rating_vote_count,
            'timeDuration': time_duration,
            'description': description,
            'director': director,
            'writer': writer,
            'stars': stars,
            'playbackURL': playback_url,
            'releaseDate': release_date,
            'countryOfOrigin': country_of_origin,
            'languages': languages,
            'productionBudget': production_budget,
            'worldwideGross': worldwide_gross,
            'topCasts': top_casts
        }

    except (IndexError, KeyError, TypeError) as e:
        print(f"Data extraction error: {e}")
        return {}


@app.route('/api/search', methods=['GET'])
def search_movie():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    print(search_By_Name(query))
    return jsonify(search_By_Name(query))


@app.route('/api/movie', methods=['GET'])
def get_movie_data():
    imdb_id = request.args.get('id')

    if not imdb_id:
        return jsonify({'error': 'IMDb ID is required'}), 400

    url = f"https://m.imdb.com/title/{imdb_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})

        if script_tag:
            json_content = script_tag.string
            data = json.loads(json_content)
            pageProps = data.get('props', {}).get('pageProps', {})
            foldData = pageProps.get('aboveTheFoldData', {})
            
            extracted_data = extract_data(foldData, pageProps)
            return jsonify(extracted_data)
        else:
            return jsonify({'error': "Script tag with id '__NEXT_DATA__' not found."}), 404

    except requests.RequestException as e:
        return jsonify({'error': f"Request failed: {e}"}), 500
    except json.JSONDecodeError as e:
        return jsonify({'error': f"JSON decode error: {e}"}), 500
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
