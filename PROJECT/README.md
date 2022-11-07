# How to run
0. Install conda -- you will run your app from it.
1. Install conda env using `conda env create -f conda-env.yml`.
2. Activate conda shell: `conda activate slack-bot`
3. Create .env file that will store your BOT_TOKEN, APP_TOKEN, SIGNING_SECRET, JIRA_API_KEY, CONNECTION_STRING
4. Run the app with: `python main.py`.
Signing secret and app token can be taken from https://api.slack.com/apps.
Bot token is given when adding bot to slack workspace.