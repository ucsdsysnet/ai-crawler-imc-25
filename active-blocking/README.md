# Active Blocking Driver
This Python script initiates instances of headless Chrome, automated with Selenium.

The list of user-agent strings to check are defined [here](https://github.com/ucsdsysnet/ai-crawler-imc-25/blob/fd35824558dc72621a8540cf0849a065857d29e9/active-blocking/active_blocking_driver.py#L57). Right now it is configured to check a Claudebot UA (AI case) and a vanilla Chrome UA (control case).

The list of websites to check are defined [here](https://github.com/ucsdsysnet/ai-crawler-imc-25/blob/fd35824558dc72621a8540cf0849a065857d29e9/active-blocking/active_blocking_driver.py#L56)

The results are saved in the `responses` dict, and can be easily saved to JSON.
The `responses` dict is keyed by the website, and the value is another dict containing the HTTP status code, and whether or not a Cloudflare Block or Challenge page is detected.

