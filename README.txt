# DEPLOYING THE APP
appcfg.py -A bandpmoney -V v1 update ./

# Remote api shell
remote_api_shell.py -s bandpmoney.appspot.com

# starting local server
dev_appserver.py Expenses



oauth2client.client.ApplicationDefaultCredentialsError: The Application Default Credentials are not available. They are available if running in Google Compute Engine. Otherwise, the environment variable GOOGLE_APPLICATION_CREDENTIALS must be defined pointing to a file defining the credentials. See https://developers.google.com/accounts/docs/application-default-credentials for more information.

D:\Arnaud\Github\Expenses>