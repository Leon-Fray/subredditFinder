import requests
import csv
import os
import time
import random

keywords_file = input("Enter the path to your keywords text file (default: keywords.txt): ").strip()
if not keywords_file:
    keywords_file = 'keywords.txt'

try:
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: File '{keywords_file}' not found.")
    exit(1)

if not keywords:
    print("Error: No keywords found in file.")
    exit(1)

print(f"Found {len(keywords)} keywords to process: {', '.join(keywords)}\n")

master_filename = 'subList.csv'
file_exists = os.path.isfile(master_filename)
total_nsfw_added = 0

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

for idx, keyword in enumerate(keywords, 1):
    print(f"[{idx}/{len(keywords)}] Processing keyword: '{keyword}'")
    
    url = f"https://www.reddit.com/subreddits/search.json?q={keyword}&limit=100&include_over_18=on&raw_json=1"
    headers = {'User-agent': random.choice(user_agents)}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        nsfw_subreddits_data = []
        all_results = len(data['data']['children'])
        nsfw_count = 0
        
        for sub in data['data']['children']:
            sub_data = sub['data']
            if sub_data.get('over18', False):
                nsfw_count += 1
                nsfw_subreddits_data.append({
                    'keyword': keyword,
                    'name': sub_data['display_name'],
                    'title': sub_data['title'],
                    'subscribers': sub_data['subscribers'],
                    'nsfw': sub_data['over18'],
                    'url': f"https://reddit.com/r/{sub_data['display_name']}"
                })
        
        print(f"  Found {all_results} total results, {nsfw_count} NSFW")
        
        if nsfw_subreddits_data:
            with open(master_filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['keyword', 'name', 'title', 'subscribers', 'nsfw', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                    file_exists = True
                
                writer.writerows(nsfw_subreddits_data)
            
            total_nsfw_added += len(nsfw_subreddits_data)
            print(f"  ✓ Added {len(nsfw_subreddits_data)} NSFW subreddits")
            
            for sub in nsfw_subreddits_data[:3]:
                print(f"    - r/{sub['name']}: {sub['subscribers']} subscribers")
            if len(nsfw_subreddits_data) > 3:
                print(f"    ... and {len(nsfw_subreddits_data) - 3} more")
        else:
            print(f"  ✗ No NSFW subreddits found in results")
        
        if idx < len(keywords):
            wait_time = random.uniform(3, 6)
            print(f"  Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"  ⚠ Rate limited! Waiting 60 seconds before retrying...")
            time.sleep(60)
            print(f"  Retrying '{keyword}'...")
            try:
                headers = {'User-agent': random.choice(user_agents)}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                nsfw_subreddits_data = []
                for sub in data['data']['children']:
                    sub_data = sub['data']
                    if sub_data.get('over18', False):
                        nsfw_subreddits_data.append({
                            'keyword': keyword,
                            'name': sub_data['display_name'],
                            'title': sub_data['title'],
                            'subscribers': sub_data['subscribers'],
                            'nsfw': sub_data['over18'],
                            'url': f"https://reddit.com/r/{sub_data['display_name']}"
                        })
                
                if nsfw_subreddits_data:
                    with open(master_filename, 'a', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['keyword', 'name', 'title', 'subscribers', 'nsfw', 'url']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        if not file_exists:
                            writer.writeheader()
                            file_exists = True
                        
                        writer.writerows(nsfw_subreddits_data)
                    
                    total_nsfw_added += len(nsfw_subreddits_data)
                    print(f"  ✓ Retry successful! Added {len(nsfw_subreddits_data)} NSFW subreddits")
                else:
                    print(f"  ✓ Retry successful but no NSFW results")
            except Exception as retry_error:
                print(f"  ✗ Retry failed: {retry_error}")
        else:
            print(f"  ✗ Error processing '{keyword}': {e}")
        continue
    except Exception as e:
        print(f"  ✗ Error processing '{keyword}': {e}")
        continue

print(f"\n{'='*50}")
print(f"Processing complete!")
print(f"Total NSFW subreddits added: {total_nsfw_added}")
print(f"Data appended to: '{master_filename}'")
print(f"{'='*50}")
