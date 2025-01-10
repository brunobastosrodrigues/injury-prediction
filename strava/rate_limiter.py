import time

API_REQUEST_LIMIT = 100  # Max requests per 15 minutes
RATE_LIMIT_INTERVAL = 15 * 60  # 15 minutes in seconds
REQUEST_COUNT = 0
START_TIME = time.time()

def check_rate_limit():
    global REQUEST_COUNT, START_TIME

    if REQUEST_COUNT >= API_REQUEST_LIMIT:
        elapsed_time = time.time() - START_TIME
        if elapsed_time < RATE_LIMIT_INTERVAL:
            sleep_time = RATE_LIMIT_INTERVAL - elapsed_time
            # Print message showing that the limit has been reached and how long to wait
            print(f"API rate limit reached. You have made {REQUEST_COUNT} requests in the last 15 minutes.")
            print(f"Sleeping for {sleep_time:.2f} seconds until the limit resets...")
            time.sleep(sleep_time)
            # Reset request count and start time after waiting
            REQUEST_COUNT = 0
            START_TIME = time.time()
        else:
            # If the time window has passed, reset the counter
            REQUEST_COUNT = 0
            START_TIME = time.time()
