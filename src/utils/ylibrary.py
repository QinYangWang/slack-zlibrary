import requests
import os
import boto3
from botocore.exceptions import NoCredentialsError
from time import sleep


s3 = boto3.client('s3')
# Use get() method to return None if environment variable is not set
bucket = os.environ.get('BUCKET_NAME')

def get_presigned_url(user: str, object_name: str, expiration: int):
    try:
        response = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': f'{user}/{object_name}'
            },
            ExpiresIn=expiration
        )
        download_msg = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Your book: {object_name} is ready. download link is <{response}|here>."
                    }
                }
            ]
        }
        return download_msg
    except NoCredentialsError:
        return "AWS credentials not configured!"


def search(keyword: str, page: int = 1, sensitive: bool = False):
    headers = {}
    message = {
        "blocks": []
    }
    json_data = {
        'keyword': keyword,
        'page': page,
        'sensitive': sensitive
    }
    response = requests.post(
        'https://api.ylibrary.org/api/search/', headers=headers, json=json_data)
    try:
        # Raise an exception if the POST request returns an error status code
        response.raise_for_status()
        response_data = response.json()

        book_list_start = [
            {
                "type": "section",
                "text": {
                        "type": "plain_text",
                    "emoji": True,
                    "text": "Here are the results I found:"
                }
            },
            {
                "type": "divider"
            },
        ]

        book_list_end = [
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"<< prev({page - 1 if page > 1 else page})",
                            "emoji": True
                        },
                        "value": f"page={page - 1 if page > 1 else page}&keyword={keyword}",
                        "action_id": "prev_page"
                    },

                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"- {page} -",
                            "emoji": True
                        }
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"next({page + 1}) >>",
                            "emoji": True
                        },
                        "value": f"page={page + 1}&keyword={keyword}",
                        "action_id": "next_page"
                    }
                ]
            }
        ]
        book_list = []

        for book in response_data['data']:
            item = {
                "type": "section",
                "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*{book.get('title')}*\n{book.get('author', 'unknown')}\n{book.get('extension', 'unknown')}"
                        },

                ],
                "accessory":
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Download"
                    },
                    "style": "primary",
                    "value": f"id={book['id']}&source={book['source']}&title={book.get('title').replace(' ', '')}",
                    "action_id": 'download_book'
                }
            }
            book_list.append(item)
        message['blocks'] = book_list_start + book_list + book_list_end
        return message
    except requests.exceptions.RequestException as e:
        return f"An error occurred during the search request: {str(e)}"


def download(id: int, source: str, user: str):
    headers = {}
    json_data = {
        'id': id,
        'source': source
    }
    detail_response = requests.post('https://api.ylibrary.org/api/detail/', headers=headers, json=json_data)
    try:
        # Raise an exception if the POST request returns an error status code
        if detail_response.status_code == 429:
            sleep(1)
            detail_response = requests.post('https://api.ylibrary.org/api/detail/', headers=headers, json=json_data)
        detail_response.raise_for_status()
        response_data = detail_response.json()
        if response_data.get('ipfs_cid', None) and response_data.get('title', None) and response_data.get('extension', None):
            url = f"https://cloudflare-ipfs.com/ipfs/{response_data['ipfs_cid']}"
            key = f"{response_data['title']}.{response_data['extension']}".replace(' ', '')
            ipfs_download_response = requests.get(url, timeout=10)
            ipfs_download_response.raise_for_status()
            try:
                s3.put_object(
                    Body=ipfs_download_response.content,
                    Bucket=bucket,
                    Key=f'{user}/{key}',
                )
                return get_presigned_url(user, key, 3600)
            except FileNotFoundError:
                return "Book not found. Please try another!"
            except NoCredentialsError:
                return "AWS credentials not configured!"
            except Exception as e:
                return str(e)
        else:
            return 'Book not found. Please try another!'
    except requests.exceptions.RequestException as e:
        print(str(e))
        return 'Book download failed. Please try another!'
