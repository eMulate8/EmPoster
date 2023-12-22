# EmPoster
 <b>Bot for writing posts in telegram channel</b>
 
 The bot intercepts messages from the Twitter feed, discord server, news from the sites cointelegraph, coindesk and bitcoinmagazine, monitors Google trends and launches a neural network to analyze the movement of the price of bitcoin. 
 The results are posted to the channel in a telegram.

 In some countries, a permanent VPN connection is required for the bot to work.
 
 How to use this bot
 
	Preparing the environment
		
		Install all necessery python libraries:
			
			pip install pytesseract
			pip install pyautogui
			pip install openai
			pip install mss
			pip install numpy
			pip install psutil
			pip install pywin32
			pip install opencv-python
			pip install webdriver-manager
			pip install tensorflow
			pip install wmi
			pip install discord
			pip install telethon
			pip install beautifulsoup4
			pip install selenium
			pip install requests
			pip install keras
			pip install pillow
			pip install twitter-api-client
			pip install wget
		
		Install pytesseract packege for your system (need only English language)
			
			https://tesseract-ocr.github.io/tessdoc/Installation.html
		
		Install Firefox
			
			https://www.mozilla.org/en-US/firefox/new/
			
		Install Discord Desktop
		
			https://discord.com/download
		
	
	Prepearing to lunch bot
	
		Capturing messages from any source can be disabled; to do this, edit the command in the async_main.py file removing unnecessary task launches (run_task()): 
		
			await asyncio.gather(run_task(price_model.nn_bot, 8), run_task(news.news, every_ten_minutes),
							  run_task(trends.trends, 9, 18),
							  run_task(twitter_data.twitter, every_ten_minutes),
							  run_task(midjorney.midjorney, random_three_to_four))
	
		With default settings, you will need to do the following things before launching the bot
		
		You have to get Telegram api keys:
			 
			- Login to your Telegram account (https://my.telegram.org/auth) with the phone number of the developer account to use.
			- Click under API Development tools.
			- A Create new application window will appear. Fill in your application details. There is no need to enter any URL, and only the first two fields (App title and Short name) can currently be changed later.
			- Click on Create application at the end. Remember that your API hash is secret and Telegram won’t let you revoke it. Don’t post it anywhere!
		
		You need a telegram session file, which will be created as soon as you connect your telegram account to the bot.

		You need to create a discord bot, get its token and add this bot to your discord server.
		
		You need to register an openai account and get an API key.
		
		You need to go to your Twitter account in your browser and use extensions to copy Twitter cookies.
		
		Fill in the settings.py file with the received data.
		
		When the bot is running, the discord window must be open at all times. Using xy.py you need to find the coordinates of the upper left corner of your discord server icon and calculate the height and width of the frame to recognize the server name.
		
		Name the server with one or two characters, this will make it easier for you to configure the bot. Add the found numeric values to the settings.py file in the variables with "GRAB" in the name.
		
		Similarly, find and enter the coordinates of the center of the server icon (in variables with “CLICK” in the name) and the coordinates of the field for writing a message to the server (in variables with “ENTER_FIELD” in the name)
		
		If there are no problems recognizing the discord server, then leave the values of the variables with “HSV” in the name as they are. Otherwise, adjust the values using color.py so that the image is best seen in the 'res' window.
			
		
		
		
		
			
			
		
		
		
