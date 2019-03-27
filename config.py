import os

client_id   = '' # your bot's client ID
token = '' # your bot's token
carbon_key = '' # your bot's key on carbon's site
bots_key = '' # your key on bots.discord.pw
postgresql = 'postgresql://user:password@host/database' # your postgresql info from above
challonge_api_key = '...' # for tournament cog

chromedriver_path = ''
global_bot_admins = []
handout_url = ''
handout_key = ''

if ('DISCORD_TOKEN' in os.environ):
    token = os.environ['DISCORD_TOKEN']
if ('POSTGRESQL_URI' in os.environ):
	postgresql = os.environ['POSTGRESQL_URI']

if ('CHROMEDRIVER_PATH' in os.environ):
    chromedriver_path = os.environ['CHROMEDRIVER_PATH']

# TODO The following settings will be moved from ENVIRONMENT variables to stored(db?) configurations

if ('GLOBAL_BOT_ADMINS' in os.environ):
    global_bot_admins = os.environ['GLOBAL_BOT_ADMINS'].split(':')
if ('ROLL20_JOURNAL' in os.environ):
    handout_url = os.environ['ROLL20_JOURNAL']
if ('ROLL20_KEY' in os.environ):
    handout_key = os.environ['ROLL20_KEY']

#TODO Print out configurations if called directly?

if __name__ == '__main__':
	pass