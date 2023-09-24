# Twitter Timeline Screenshot Stitcher

This script captures screenshots of a user's Twitter timeline and stitches them together into a single image. It's useful for archiving a user's Twitter feed at a given point in time.

## Prerequisites

- Python 3.x
- Google Chrome Browser

## Dependencies

Install the required packages:

\```bash
pip install selenium Pillow
\```

You will also need to download the appropriate [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) for your version of Chrome.

## Capturing Twitter Cookies

To run this script, you'll need to provide it with your Twitter session cookies. This is essential to access and scroll through the Twitter timeline programmatically. Here's how you can capture the cookies:

1. **Install a Cookie Editor Extension**: Add a cookie editor extension to your browser. For Chrome, you might consider [EditThisCookie](http://www.editthiscookie.com/).

2. **Log in to Twitter**: Visit [Twitter](https://twitter.com/) and log in with your account.

3. **Open the Cookie Editor**: Once logged in, click on the cookie editor extension icon.

4. **Export Cookies**:
    - In the cookie editor, find an option to export or copy all cookies to clipboard.
    - Copy the cookies.

5. **Create a JSON File**: 
    - Open a text editor and paste the copied cookies.
    - Save this file as `cookies.json` in the same directory as the script.

## Running the Script

1. Navigate to the script's directory:

\```bash
cd path_to_script_directory
\```

2. Run the script:

\```bash
python twitter_timeline_stitcher.py --username <YOUR_TWITTER_USERNAME>
\```

For debugging and more options, see:

\```bash
python twitter_timeline_stitcher.py --help
\```

## Note

Web scraping is subject to legal and ethical considerations. Ensure you have the right permissions and are in compliance with Twitter's terms of use and robots.txt. Always be respectful of the platforms you're interacting with.
