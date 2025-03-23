from setuptools import setup, find_packages

setup(
    name="kudos-scraping",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "requests",
        "beautifulsoup4",
        "mysql-connector-python",
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "gspread",
        "python-dotenv",
        "tenacity",
    ],
    python_requires=">=3.8",
) 